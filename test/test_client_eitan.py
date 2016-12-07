import requests
#from bcrypt import hashpw, gensalt

#pwd = "ptest1"
#hashed = hashpw(pwd.encode('utf-8'), gensalt())
#print (hashed)    # save this value to the database for this user

seqs={'user':'user9','pwd':'puser9'}
seqs_user={'user':'eitan','pwd':'YPS144','name':'Eitan','description':'aaaa','email':'eitanozel@gmail.com','publish':'y'}
#seqs_user={'user':'user8','pwd':'puser8','name':'name8','description':'description8','email':'user8@gmail.com','publish':'y'}
#seqs={'user':'na','pwd':''}
#seqs={'a':'a'}
#seqs={''}
#c=requests.get('http://amnonim.webfactional.com/scdb_develop/users/add_temp_users')
#c=requests.get('http://amnonim.webfactional.com/scdb_develop/users/test_user_login',json=seqs)
#c=requests.get('http://amnonim.webfactional.com/scdb_develop/users/test_user_login')
#c=requests.get('http://127.0.0.1:5000/users/test_user_login',json=seqs)
#c=requests.post('http://127.0.0.1:5000/users/send_mail_test')
#c=requests.post('http://amnonim.webfactional.com/scdb_develop/users/send_mail_test')

#seq_pwd={'user':'eitan'}
#c=requests.get('http://127.0.0.1:5000/users/forgot_password',json=seq_pwd)

#seqs={'user':'user1','pwd':'3QCS3W'}
#c=requests.post('http://127.0.0.1:5000/users/test_user_login',json=seqs)

#c=requests.post('http://127.0.0.1:5000/users/register_user',json=seqs_user)
#c=requests.post('http://amnonim.webfactional.com/scdb_develop/users/register_user',json=seqs_user)
#c=requests.post('http://amnonim.webfactional.com/scdb_develop/users/test_user_login',json=seqs_user)

#rdata={}
#rdata['sequence']='tacggagggtgcgagcgttaatcggaataactgggcgtaaagggcacgcaggcggtgacttaagtgaggtgtgaaagccccgggcttaacctgggaattgcatttcatactgggtcgctagagtactttagggaggggtagaattccacg'



#rdata['sequence']='tacggagggtgcgagcgttaatcggaataactgggcgtaaagggcacgcaggcggtgacttaagtgaggtgtgaaagccccgggcttaacctgggaattgcatttcatactgggtcgctagagtactttagggaggggtagaattccacg'
#c=requests.get('http://amnonim.webfactional.com/scdb_develop/sequences/get_annotations',json=rdata)
#c=requests.get('http://amnonim.webfactional.com/develop/sequences/get_annotations',json=rdata)
#c=requests.get('http://127.0.0.1:5000/sequences/get_annotations',json=rdata)
#c=requests.get('http://amnonim.webfactional.com/scdb_develop/sequences/get_annotations',json=rdata)
#rdata={}
#rdata['userid']=0
#c=requests.get('http://amnonim.webfactional.com/scdb_develop/users/get_user_public_information',json=rdata)
#c=requests.get('http://127.0.0.1:5001/users/get_user_public_information',json=rdata)
seq_pwd={'userid':0}
c=requests.get('http://127.0.0.1:5000/users/get_user_public_information',json=seq_pwd)
c=requests.post('http://127.0.0.1:5000/users/get_user_id',json=seq_pwd)
#c=requests.get('http://amnonim.webfactional.com/scdb_develop/users/get_user_public_information',json=seq_pwd)

#c=requests.get('http://amnonim.webfactional.com/scdb_develop/users/forgot_password',json=seq_pwd)
#c=requests.post('http://amnonim.webfactional.com/scdb_develop/users/register_user',json=seqs_user)
#c=requests.get('http://amnonim.webfactional.com/site/main')
#c=requests.get('http://127.0.0.1:5000/site/main')
print(c.content)

#c=requests.post('http://127.0.0.1:5000/users/add_temp_users',json=seqs)
#c=requests.post('http://127.0.0.1:5000/users/add_temp_users2')
#c=requests.post('http://amnonim.webfactional.com/scdb_develop/users/add_temp_users')
#c=requests.post('http://amnonim.webfactional.com/scdb_develop/users/get_user_id',json=seqs)
#c=requests.post('http://127.0.0.1:5000/users/get_user_id',json=seqs)


#print(c.content)

#c=requests.get('http://amnonim.webfactional.com/scdb_main/sequences/getid',json=seqs)
#c=requests.get('http://127.0.0.1:5000/sequences/getid',json=seqs)
#c=requests.get('http://127.0.0.1:5000/sequences/get_annotations',json=seqs)

#seqs={'user':'user3','pwd':'puser3','sequence':'CCAGG'}
#seqs={'user':'na1','pwd':'','sequence':'CCAGG'}
#seqs={'sequence':'CCAGG'}
#c=requests.get('http://127.0.0.1:5000/sequences/getid',json=seqs)

#c=requests.post('http://127.0.0.1:5000/users/add_temp_users')

#seqs={'user':'user1','pwd':'puser1'}
#c=requests.post('http://127.0.0.1:5000/users/test_user_login',json=seqs)
#c=requests.post('http://127.0.0.1:5000/users/get_user_id',json=seqs)

#seqs={'user':'user1','pwd':'puser1'}
#c=requests.get('http://amnonim.webfactional.com/scdb/sequences/test_user_login',json=seqs)

# and to see the results:

#print(c.content)

###SET search_path = annotationschematest, pg_catalog;

###CREATE extension IF NOT EXISTS pgcrypto SCHEMA annotationschematest;
###update userstable set passwordhash=crypt('', gen_salt('bf')) where id=0;


#seqs_user={'user':'user9','pwd':'puser9','name':'name9','description':'description9','email':'user9@gmail.com','publish':'y'}
#c=requests.post('http://amnonim.webfactional.com/scdb_develop/users/register_user',json=seqs_user)

