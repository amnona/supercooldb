from collections import defaultdict
import psycopg2

import primers
from utils import debug
import dbannotations

# length for the seed sequence
# used for fast searching of sub sequences
SEED_SEQ_LEN = 100


def AddSequences(con, cur, sequences, taxonomies=None, ggids=None, primer='V4', commit=True):
    """
    Add sequence entries to database if they do not exist yet
    input:
    con,cur : database connection and cursor
    sequences: list of str
        the sequences to add
    taxonomies: list of str (optional)
        taxonomy of each sequence or None to add NA
    ggids: list of int (optional)
        list of GreenGenes id for each sequence or None to add 0
    primer: str (optional)
        Name of the primer (from PrimersTable). default is V4
    commit : bool (optional)
        True (default) to commit, False to wait with the commit

    output:
    errmsg : str
        "" if ok, error msg if error encountered
    seqids : list of int or None
        list of the new ids or None if error enountered
    """
    # get the primer region id
    seqids = []
    numadded = 0
    idprimer = primers.GetIdFromName(con, cur, primer)
    if idprimer < 0:
        debug(2, 'primer %s not found' % primer)
        return "primer %s not found" % primer, None
    debug(1, 'primerid %s' % idprimer)
    try:
        for idx, cseq in enumerate(sequences):
            if len(cseq) < SEED_SEQ_LEN:
                errmsg = 'sequence too short (<%d) for sequence %s' % (SEED_SEQ_LEN, cseq)
                debug(4, errmsg)
                return errmsg, None
            # test if already exists, skip it
            err, cseqid = GetSequenceId(con, cur, sequence=cseq, idprimer=idprimer, no_shorter=True, no_longer=True)
            if len(cseqid) == 0:
                # not found, so need to add this sequence
                if taxonomies is None:
                    ctax = 'na'
                else:
                    ctax = taxonomies[idx].lower()
                if ggids is None:
                    cggid = 0
                else:
                    cggid = ggids[idx]
                cseq = cseq.lower()
                cseedseq = cseq[:SEED_SEQ_LEN]
                cur.execute('INSERT INTO SequencesTable (idPrimer,sequence,length,taxonomy,ggid,seedsequence) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id', [idprimer, cseq, len(cseq), ctax, cggid, cseedseq])
                cseqid = cur.fetchone()
                numadded += 1
            if len(cseqid) > 1:
                debug(8, 'AddSequences - Same sequence appears twice in database: %s' % cseq)
            seqids.append(cseqid[0])
        if commit:
            con.commit()
        debug(3, "Added %d sequences (out of %d)" % (numadded, len(sequences)))
        return "", seqids
    except psycopg2.DatabaseError as e:
        debug(7, 'database error %s' % e)
        return "database error %s" % e, None


def SeqFromID(con, cur, seqids):
    '''Get the information about the sequence.
    Get the sequence (ACGT) and taxonomy from sequence id or list of sequence ids

    Parameters
    ----------
    con, cur
    seqids : int or list of int
        the ids to get the sequences for

    Returns
    -------
    sequences : list of dict (one per sequence). contains:
        'seq' : str (ACGT)
            the sequence
        'taxonomy' : str
            the taxonomy of the sequence or '' if unknown
    '''
    if isinstance(seqids, int):
        seqids = [seqids]
    sequences = []
    for cseqid in seqids:
        cur.execute("SELECT sequence,coalesce(taxdomain,''),coalesce(taxphylum,''),  coalesce(taxclass,''),coalesce(taxorder,''),coalesce(taxfamily,''), coalesce(taxgenus,'') as taxonomy_str FROM SequencesTable WHERE id=%s", [cseqid])
        
        if cur.rowcount == 0:
            sequences.append({'seq': ''})
            continue
        res = cur.fetchone()
        
        firstTax = True
        taxStr = ''
        list_of_pre_str = ["d__","p__","c__","o__","f__","g__"]
        for idx, val in enumerate(list_of_pre_str):
            if res[idx + 1]:
                if firstTax == False :
                    taxStr += ';'
                taxStr += val + res[idx + 1]            
                firstTax = False
        
        cseqinfo = {'seq': res[0], 'taxonomy': taxStr}
        sequences.append(cseqinfo)
    return '', sequences


def GetSequencesId(con, cur, sequences, no_shorter=False, no_longer=False):
    """
    Get sequence ids for a sequence or list of sequences

    input:
    con,cur : database connection and cursor
    sequences : list of str (ACGT sequences)
    no_shorter : bool (optional)
        False (default) to enable shorter db sequences matching sequence, True to require at least length of query sequence
    no_longer : bool (optional)
        False (default) to enable longer db sequences matching sequence, True to require at least length of database sequence

    output:
    errmsg : str
        "" if ok, error msg if error encountered
    ids : ilist of int
        the list of ids for each sequence (-1 for sequences which were not found)
    """
    if isinstance(sequences, str):
        sequences = [sequences]
    ids = []
    for cseq in sequences:
        err, cid = GetSequenceId(con, cur, cseq, no_shorter=no_shorter, no_longer=no_longer)
        if err:
            # skip - or should we abort and return an error?
            continue
        ids.extend(cid)
    return "", ids


def GetSequenceIdFromGG(con, cur, ggid):
    '''
    Get the sequence id for a given greengenes id (from rep. set 97%)

    Parameters
    ----------
    con,cur : database connection and cursor
    ggid : int
        The greengenes (rep_set 97%) identifier of the sequence

    Returns
    -------
    errmsg : str
        "" if ok, error msg if error encountered
    sid : list of int
        the ids of the matching sequences (empty tuple if not found)
        Note: can be more than one as several dbbact sequences can map to same ggid
    '''
    sid = []

    debug(1, 'get id for ggid %d' % ggid)
    cur.execute('SELECT id FROM SequencesTable WHERE ggid=%s', [ggid])
    if cur.rowcount == 0:
        errmsg = 'ggid %s not found in database' % ggid
        debug(1, errmsg)
        return errmsg, sid

    res = cur.fetchall()
    for cres in res:
        resid = cres[0]
        sid.append(resid)

    debug(1, 'found %d sequences for ggid %d' % (len(sid),ggid))
    return '', sid


def GetSequenceId(con, cur, sequence, idprimer=None, no_shorter=False, no_longer=False):
    """
    Get sequence ids for a sequence

    input:
    con,cur : database connection and cursor
    sequence : str (ACGT sequences)
    idprimer : int (optional)
        if supplied, verify the sequence is from this idPrimer
    no_shorter : bool (optional)
        False (default) to enable shorter db sequences matching sequence, True to require at least length of query sequence
    no_longer : bool (optional)
        False (default) to enable longer db sequences matching sequence, True to require at least length of database sequence

    output:
    errmsg : str
        "" if ok, error msg if error encountered
    sid : list of int
        the ids of the matching sequences (empty tuple if not found)
        Note: can be more than one as we also look for short subsequences / long supersequences
    """
    # check if the sequence is made only of digits assume it is a greengenes id
    if sequence.isdigit():
        debug(1, 'getting id for ggid %s' % sequence)
        return GetSequenceIdFromGG(con, cur, int(sequence))

    sid = []
    cseq = sequence.lower()
    if len(cseq) < SEED_SEQ_LEN:
        errmsg = 'sequence too short (<%d) for sequence %s' % (SEED_SEQ_LEN, cseq)
        debug(4, errmsg)
        return errmsg, sid

    # look for all sequences matching the seed
    cseedseq = cseq[:SEED_SEQ_LEN]
    cur.execute('SELECT id,sequence FROM SequencesTable WHERE seedsequence=%s', [cseedseq])
    if cur.rowcount == 0:
        errmsg = 'sequence %s not found' % sequence
        debug(1, errmsg)
        return errmsg, sid

    cseqlen = len(cseq)
    res = cur.fetchall()
    for cres in res:
        resid = cres[0]
        resseq = cres[1]
        if no_shorter:
            if len(resseq) < cseqlen:
                continue
            comparelen = cseqlen
        else:
            comparelen = min(len(resseq), cseqlen)
        if no_longer:
            if len(resseq) > cseqlen:
                continue
        if cseq[:comparelen] == resseq[:comparelen]:
            if idprimer is None:
                sid.append(resid)
            cur.execute('SELECT idPrimer FROM SequencesTable WHERE id=%s LIMIT 1', [resid])
            res = cur.fetchone()
            if res[0] == idprimer:
                sid.append(resid)
    if len(sid) == 0:
        errmsg = 'sequence %s not found' % sequence
        debug(1, errmsg)
        return errmsg, sid
    return '', sid

    # # if no regionid specified, fetch only 1 (faster)
    # if idprimer is None:
    #   cur.execute('SELECT id FROM SequencesTable WHERE sequence=%s LIMIT 1',[cseq])
    #   if cur.rowcount==0:
    #       sid=-1
    #       debug(2,'sequence %s not found' % sequence)
    #   else:
    #       sid=cur.fetchone()[0]
    #       debug(1,'sequence %s found id %d' % (sequence,sid))
    #   return "",sid
    # # regionid was specified, so test all matching sequences
    # cur.execute('SELECT id,idPrimer FROM SequencesTable WHERE sequence=%s LIMIT 1',[cseq])
    # for cres in cur:
    #   if cres[1]==idprimer:
    #       sid=cres[0]
    #       debug(1,'sequence %s found with primer. id %d' % (sequence,sid))
    #       return "",sid
    # debug(2,'sequence %s not found with primer. non primer matches: %d' % (sequence,cur.rowcount))
    # return 'sequence %s not found with primer. non primer matches: %d' % (sequence,cur.rowcount),-1


def GetTaxonomyAnnotationIDs(con, cur, taxonomy, userid=None):
    '''
    Get annotationids for all annotations containing any sequence matching the taxonomy (substring)

    Parameters
    ----------
    con,cur
    taxonomy : str
        the taxonomy substring to look for
    userid : int (optional)
        the userid of the querying user (to enable searching private annotations)

    Returns
    -------
    annotationids : list of (int, int) (annotationid, count)
        list containing the ids of all annotations that contain a sequence with the taxonomy and the count of number of sequences from the taxonomy in that annotation
    seqids : list of int
        list of the sequenceids that have this annotation
    '''
    taxonomy = taxonomy.lower()
    taxStr = taxonomy 
    debug(1, 'GetTaxonomyAnnotationIDS for taxonomy %s' % taxonomy)
    cur.execute('SELECT id from SequencesTable where (taxrootrank ILIKE %s OR taxdomain ILIKE %s OR taxphylum ILIKE %s OR taxclass ILIKE %s OR taxfamily ILIKE %s OR taxgenus ILIKE %s OR taxorder ILIKE %s)', [taxStr,taxStr,taxStr,taxStr,taxStr,taxStr,taxStr])
    res = cur.fetchall()
    seqids = []
    for cres in res:
        seqids.append(cres[0])
    debug(1, 'found %d matching sequences for the taxonomy' % len(seqids))
    annotationids_dict = defaultdict(int)
    for cseq in seqids:
        cur.execute('SELECT annotationid from sequencesAnnotationTable where seqid=%s', [cseq])
        res = cur.fetchall()
        for cres in res:
            annotationids_dict[cres[0]] += 1
    # NOTE: need to add user validation for the ids!!!!!!
    debug(1, 'found %d unique annotations for the taxonomy' % len(annotationids_dict))
    annotationids = []
    for k, v in annotationids_dict.items():
        annotationids.append((k, v))
    return '', annotationids, seqids


def GetTaxonomyAnnotations(con, cur, taxonomy, userid=None):
    '''
    Get annotations for all annotations containing any sequence matching the taxonomy (substring)

    Parameters
    ----------
    con,cur
    taxonomy : str
        the taxonomy substring to look for
    userid : int (optional)
        the userid of the querying user (to enable searching private annotations)

    Returns
    -------
    annotations : list of tuples (annotation, counts)
        list containing the details for all annotations that contain a sequence with the taxonomy
        annotation - (see dbannotations.GetAnnotationsFromID() )
        counts - the number of sequences from taxonomy appearing in this annotations
    seqids : list of int
        list of the sequenceids which have this taxonomy
    '''
    debug(1, 'GetTaxonomyAnnotations for taxonomy %s' % taxonomy)
    # get the annotation ids
    err, annotationids, seqids = GetTaxonomyAnnotationIDs(con, cur, taxonomy, userid)
    if err:
        errmsg = 'Failed to get annotationIDs for taxonomy %s: %s' % (taxonomy, err)
        debug(6, errmsg)
        return errmsg, None
    # and get the annotation details for each
    annotations = []
    for cres in annotationids:
        cid = cres[0]
        ccount = cres[1]
        err, cdetails = dbannotations.GetAnnotationsFromID(con, cur, cid)
        if err:
            debug(6, err)
            continue
        annotations.append((cdetails, ccount))
    debug(1, 'got %d details' % len(annotations))
    return '', annotations, seqids


def GetSequenceWithNoTaxonomyID(con, cur):
    '''
    Get sequence with no taxonomy (if any)

    Parameters
    ----------
    con,cur

    Returns
    -------
    sequence id : return the sequence id
    '''
    debug(1, 'GetSequenceWithNoTaxonomy')
    
    cur.execute("select id from annotationschematest.sequencestable where (COALESCE(taxrootrank,'')='' AND COALESCE(taxdomain,'')='' AND COALESCE(taxphylum,'')='' AND COALESCE(taxclass,'')='' AND COALESCE(taxfamily,'')='' AND COALESCE(taxgenus,'')='' AND COALESCE(taxorder,'')='') limit 1")
    if cur.rowcount == 0:
        errmsg = 'no missing taxonomy'
        debug(1, errmsg)
        return errmsg, -1
    res = cur.fetchone()
    return_id = res[0]
    
    return '', return_id


def GetSequenceStrByID(con, cur, seq_id):
    '''
    Get sequence with no taxonomy (if any)

    Parameters
    ----------
    con,cur
    seq_id
    
    Returns
    -------
    sequence str : return the sequence str
    '''
    debug(1, 'GetSequenceStrByID')
    
    cur.execute("select sequence from annotationschematest.sequencestable where id=%s" % seq_id)
    if cur.rowcount == 0:
        errmsg = 'no missing taxonomy'
        debug(1, errmsg)
        return errmsg, seq_id
    res = cur.fetchone()
    return_id = res[0]
    
    return '', return_id


def AddSequenceTax(con, cur, seq_id, col, value):
    '''
    update taxonomy record value

    Parameters
    ----------
    con,cur
    seq_id
    col - taxonomyrank coloumn name
    value - taxonomyrank value
    
    Returns
    -------
    true or false
    '''
    debug(1, 'GetSequenceStrByID')
    
    try:
        cur.execute("update annotationschematest.sequencestable set %s='%s' where id=%s" % (col,value,seq_id))
        con.commit()
        return True
    except:
        return False
    
def GetSequenceTaxonomy(con, cur, sequence, region=None, userid=0):
    """
    Get taxonomy str for specific string
    
    Parameters
    ----------
    con,cur :
    sequence : str ('ACGT')
        the sequence to search for in the database
    region : int (optional)
        None to not compare region, or the regionid the sequence is from
    userid : int (optional)
        the id of the user requesting the annotations. Private annotations with non-matching user will not be returned

    Returns
    -------
    err : str
        The error encountered or '' if ok
    taxonomy: Taxonomy string
    """
    
    debug(1, 'GetSequenceTaxonomy sequence %s' % sequence)
    
    cseq = sequence.lower()
    cur.execute("SELECT coalesce(taxdomain,''),coalesce(taxphylum,''),  coalesce(taxclass,''),coalesce(taxorder,''),coalesce(taxfamily,''), coalesce(taxgenus,'') as taxonomy_str FROM SequencesTable WHERE sequence=%s", [cseq])
        
    if cur.rowcount == 0:
        ctaxinfo = {'taxonomy': taxStr}
        return '', ctaxinfo
    res = cur.fetchone()
    
    firstTax = True
    taxStr = ''
    list_of_pre_str = ["d__","p__","c__","o__","f__","g__"]
    for idx, val in enumerate(list_of_pre_str):
        if res[idx]:
            if firstTax == False :
                taxStr += ';'
            taxStr += val + res[idx]            
            firstTax = False
        
    ctaxinfo = {'taxonomy': taxStr}
    return '', ctaxinfo
