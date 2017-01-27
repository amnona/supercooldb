from collections import defaultdict
import psycopg2
import .primers
from .utils import debug
import .dbannotations

# length for the seed sequence
# used for fast searching of sub sequences
SEED_SEQ_LEN = 100


def AddSequences(con,cur,sequences,taxonomies=None,ggids=None,primer='V4',commit=True):
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
    seqids=[]
    numadded=0
    idprimer = primers.GetIdFromName(con,cur,primer)
    if idprimer<0:
        debug(2,'primer %s not found' % primer)
        return "primer %s not found" % primer,None
    debug(1,'primerid %s' % idprimer)
    try:
        for idx,cseq in enumerate(sequences):
            if len(cseq)<SEED_SEQ_LEN:
                errmsg='sequence too short (<%d) for sequence %s' % (SEED_SEQ_LEN, cseq)
                debug(4,errmsg)
                return errmsg, None
            # test if already exists, skip it
            err,cseqid=GetSequenceId(con,cur,sequence=cseq,idprimer=idprimer)
            if cseqid<=0:
                if taxonomies is None:
                    ctax='na'
                else:
                    ctax=taxonomies[idx].lower()
                if ggids is None:
                    cggid=0
                else:
                    cggid=ggids[idx]
                cseq=cseq.lower()
                cseedseq=cseq[:SEED_SEQ_LEN]
                cur.execute('INSERT INTO SequencesTable (idPrimer,sequence,length,taxonomy,ggid,seedsequence) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id',[idprimer,cseq,len(cseq),ctax,cggid,cseedseq])
                cseqid=cur.fetchone()[0]
                numadded+=1
            seqids.append(cseqid)
        if commit:
            con.commit()
        debug(3,"Added %d sequences (out of %d)" % (numadded,len(sequences)))
        return "",seqids
    except psycopg2.DatabaseError as e:
        debug(7,'database error %s' %e)
        return "database error %s" % e,None


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
        cur.execute('SELECT sequence,taxonomy FROM SequencesTable WHERE id=%s', [cseqid])
        if cur.rowcount == 0:
            sequences.append({'seq': ''})
            continue
        res = cur.fetchone()
        cseqinfo = {'seq': res[0], 'taxonomy': res[1]}
        sequences.append(cseqinfo)
    return '', sequences


def GetSequencesId(con,cur,sequences):
    """
    Get sequence ids for a sequence or list of sequences

    input:
    con,cur : database connection and cursor
    sequences : list of str (ACGT sequences)

    output:
    errmsg : str
        "" if ok, error msg if error encountered
    ids : ilist of int
        the list of ids for each sequence (-1 for sequences which were not found)
    """
    if isinstance(sequences,str):
        sequences=[sequences]
    ids=[]
    for cseq in sequences:
        err,cid=GetSequenceId(con,cur,cseq)
        if err:
            return err,None
        ids.append(cid)
    return "",ids


def GetSequenceId(con, cur, sequence, idprimer=None, use_full_lengh=False):
    """
    Get sequence ids for a sequence

    input:
    con,cur : database connection and cursor
    sequence : str (ACGT sequences)
    idprimer : int (optional)
        if supplied, verify the sequence is from this idPrimer
    use_full_length : bool (optional)
        False (default) to enable shorter db sequences matching sequence, True to require match on all of sequence length

    output:
    errmsg : str
        "" if ok, error msg if error encountered
    sid : int
        the id of the sequence (-1 if not found)
    """
    cseq = sequence.lower()
    if len(cseq) < SEED_SEQ_LEN:
        errmsg = 'sequence too short (<%d) for sequence %s' % (SEED_SEQ_LEN, cseq)
        debug(4, errmsg)
        return errmsg, -1

    # look for all sequences matching the seed
    cseedseq = cseq[:SEED_SEQ_LEN]
    cur.execute('SELECT id,sequence FROM SequencesTable WHERE seedsequence=%s', [cseedseq])
    if cur.rowcount == 0:
        sid = -1
        errmsg = 'sequence %s not found' % sequence
        debug(1, errmsg)
        return errmsg, sid

    cseqlen = len(cseq)
    res = cur.fetchall()
    for cres in res:
        resid = cres[0]
        resseq = cres[1]
        if use_full_lengh:
            if len(resseq) < cseqlen:
                continue
            comparelen = cseqlen
        else:
            comparelen = min(len(resseq), cseqlen)
        if cseq[:comparelen] == resseq[:comparelen]:
            if idprimer is None:
                return '', resid
            cur.execute('SELECT idPrimer FROM SequencesTable WHERE id=%s LIMIT 1', [resid])
            res = cur.fetchone()
            if res[0] == idprimer:
                return '', resid
    # reached here so sequence was not found
    errmsg = 'sequence %s not found' % sequence
    debug(1, errmsg)
    return errmsg, -1

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
    '''
    taxonomy = taxonomy.lower()
    debug(1, 'GetTaxonomyAnnotationIDS for taxonomy %s' % taxonomy)
    cur.execute('SELECT id from SequencesTable where taxonomy LIKE %s', ['%'+taxonomy+'%'])
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
    return '', annotationids


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
    '''
    debug(1, 'GetTaxonomyAnnotations for taxonomy %s' % taxonomy)
    # get the annotation ids
    err, annotationids = GetTaxonomyAnnotationIDs(con, cur, taxonomy, userid)
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
    return '', annotations
