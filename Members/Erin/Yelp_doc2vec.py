#--------Import libraries-----------
#-------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import string, re, random
import itertools
from random import sample
#GenSim Doc2Vec libraries:
import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import simple_preprocess
import multiprocessing
import os
cores = multiprocessing.cpu_count()
#------Display up to 200 columns & all content within each column
pd.set_option('max_columns',200)
pd.set_option('display.max_colwidth', -1)
pd.set_option('max_rows',50)

#------Load dataframe of restaurant reviews for restaurants with >25 reviews
#------and save sampled dataframe to pickle file:

#df1 = pd.read_pickle("./data/df_LVrestaurantsOpen25+.pkl")
##sample 25 reviews from each restaurant:
#df = df1.groupby('business_id').apply(lambda x: x.sample(25))
#df.to_pickle("./data/df_LVrestaurants25samples.pkl") #save sampled file


#-------Load sampled data frame with 25 reviews per restaurant
df = pd.read_pickle("./data/df_LVrestaurants25samples.pkl")
#-------Create smaller dataframe (fewer columns) for simplified viewing
dfR = df.filter(["name","address","business_id","review_id","text"])
dfR = dfR.set_index('review_id')
dfR = dfR.reset_index()
dfR.head(1)
#-------------------------------------------------------------------------------
#-----Set up & train Doc2Vec model on 25 reviews for each restaurant in dataframe
#-------------------------------------------------------------------------------
# class MyReviews(object):
#     def __iter__(self):
#         for i in range(dfR.shape[0]):
#             yield TaggedDocument(words=simple_preprocess(dfR.iloc[i,-1]), tags=[str.format(dfR.iloc[i,0])])
#
# assert gensim.models.doc2vec.FAST_VERSION > -1, "this will be painfully slow otherwise"
# #
# # if not os.path.exists('models/doc2vec.model'):
# #     print("Start training doc2vec model...")
# #     documents = MyReviews()
# #     doc2vec_model = Doc2Vec(dm=1, dbow_words=1, vector_size=200, window=8, min_count=5, workers=cores)
# #     doc2vec_model.build_vocab(documents)
# #     print("Vocab built...")
# #     doc2vec_model.train(documents, total_examples=doc2vec_model.corpus_count, epochs=doc2vec_model.epochs)
# #     print("Minutes training time:",doc2vec_model.total_train_time/60)
# #     print("Model trained!")
# #     if not os.path.exists('models'):
# #         os.makedirs('models')
# #         doc2vec_model.save('models/doc2vec.model')
# #     else:
# #         doc2vec_model.save('models/doc2vec.model')
# # else:
# #     doc2vec_model = Doc2Vec.load('models/doc2vec.model')

doc2vec_model = Doc2Vec.load('models/doc2vec.model')
#----end of model training

#-------------------------------------------------------------------------------
#-----Test dataframe with 2 sampled restaurants------

Rest_A = df.sample(1).filter(["name","address","business_id"]).set_index('business_id').reset_index()
print(Rest_A.name.values[0],",",Rest_A.address.values[0])
Rest_B = df.sample(1).filter(["name","address","business_id"]).set_index('business_id').reset_index()
print(Rest_B.name.values[0],",",Rest_B.address.values[0])

RA_df = dfR[dfR.business_id == str.format(Rest_A.business_id[0])]  #dataframe with all Restaurant A's reviews
RB_df = dfR[dfR.business_id == str.format(Rest_B.business_id[0])]  #dataframe with all Restaurant B's reviews

#----Find similarity to each restaurant----------------
RA_sim = pd.DataFrame(doc2vec_model.docvecs.most_similar(RA_df.iloc[0:25,0], topn=len(dfR)))
RA_sim.columns = ['review_id','A_sim']   #A_sim is averaged(?) over all 25 reviews for Rest_A
RA_sim = pd.merge(RA_sim,dfR,on="review_id",how="left")
RA_sim = RA_sim.groupby(by=["business_id","name","address"]).agg(['mean','median','min','max']).sort_values(by=("A_sim","median"),ascending=False).reset_index()
print("Restaurants most similar to restaurant A:")
(RA_sim.head())


RB_sim = pd.DataFrame(doc2vec_model.docvecs.most_similar(RB_df.iloc[0:25,0], topn=len(dfR)))
RB_sim.columns = ['review_id','B_sim']
RB_sim = pd.merge(RB_sim,dfR,on="review_id",how="left")
RB_sim = RB_sim.groupby(by=["business_id","name","address"]).agg(['mean','median','min','max']).sort_values(by=("B_sim","median"),ascending=False).reset_index()
print("Restaurants most similar to restaurant B:")
(RB_sim.head())

#-------------------------------------------------------------------------------
#-------------- Arrange & sort results

results = pd.merge(RA_sim,RB_sim,on=('business_id','name','address'))
results['AB_sim'] = results[[('A_sim','median'),('B_sim','median')]].mean(axis=1)
results = results.sort_values(by="AB_sim",ascending=False)
#------------------------------------------------------------------------------------------
### Dataframe with statistics for most similar restaurants to BOTH restaurant A & restaurant B
results.head()

results = results[["business_id","name","address","AB_sim"]]
results.columns = results.columns.droplevel(-1)
results.head()

cols = [50,51,52,53,54,55,56]  #remove columns from original df (columns with review text & other info)
df = df.drop(df.columns[cols],axis=1).set_index('business_id')

results = pd.merge(results,df,on=['business_id','name','address'],how="left")
results = results.drop_duplicates()
results.loc[:,'business_id':'AB_sim'].head(5)

#return(results)   #full dataframe of restaurants, metadata, and similarities to A and B

# #-------------------------------------------------------------------------------
# #---------------Find Vectors for all Reviews----------------
#
# review_idlist = dfR["review_id"].tolist()
# vectors = []
# for i in range(0,len(review_idlist)):
#     vectors.append(doc2vec_model.docvecs[i])
#
# Review_vectors = pd.DataFrame({'review_id':review_idlist, 'vectors':vectors})
#
# Review_vectors.to_pickle("ReviewVectors2.pkl")
#
# Review_vectors.head()
