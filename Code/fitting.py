#import pyreadstat as prs
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier 
import matplotlib.pyplot as plt
from dataprocessing import *



# assume we have X and y from dataprocessing

# load data
data, y, featureinfo = load_data()


subset_fns = [subset_community, subset_gender, subset_hcsci, subset_intl, subset_natlism,
                subset_other, subset_pers, subset_polit_sys, subset_race, 
                subset_social_financial]

topics = ['community', 'gender', 'healthcare/science', 'intl relations', 'nationalism',
            'miscellaneous', 'personality/values', 'political system', 'race', 'social/financial']
scores = []

#Initial fit, one-hot encoding, default RandomForest, no subset selection, single train-test-split
#random state 42
for fn in subset_fns:
    sub_data, sub_features, sub_cont = fn(data, featureinfo)
    X_prepared, encoder, y_prep = fit_prepare(data = sub_data, labels = y, cont = sub_cont)

    X_train, X_test, y_train, y_test = train_test_split(X_prepared, 
                                                        y_prep, test_size = 0.2, 
                                                        random_state = 42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    #ypred = model.predict(X_test)
    #yposterior = model.predict_proba(X_test)
    scores.append(model.score(X_test, y_test))

scores = []
# same as above except entropy loss
for fn in subset_fns:
    sub_data, sub_features, sub_cont = fn(data, featureinfo)
    X_prepared, encoder, y_prep = fit_prepare(data = sub_data, labels = y, cont = sub_cont)

    X_train, X_test, y_train, y_test = train_test_split(X_prepared, 
                                                        y_prep, test_size = 0.2, 
                                                        random_state = 42)
    model = RandomForestClassifier(criterion='entropy', max_depth=10)
    model.fit(X_train, y_train)
    #ypred = model.predict(X_test)
    #yposterior = model.predict_proba(X_test)
    scores.append(model.score(X_test, y_test))

###### HYPERPARAMETER TUNING


bestparamslistrf = []
scoresrf = []
# tune each tree
for fn in subset_fns:
    sub_data, sub_features, sub_cont = fn(data, featureinfo)
    X_prepared, encoder, y_prep = fit_prepare(data = sub_data, labels = y, cont = sub_cont)

    model = RandomForestClassifier()
    params = {'criterion' : ('gini', 'entropy'), 
               'max_depth': [1, 3, 10, 20]}
    tuner = GridSearchCV(estimator = model, param_grid = params)
    tuner.fit(X_prepared, y_prep)

    bestparamslistrf.append(tuner.best_params_)
    scoresrf.append(tuner.best_score_)

# pandas df for best parameters
bestparamsrf = pd.DataFrame(bestparamslistrf)
bestparamsrf['Subject'] = topics
bestparamsrf['Score'] = scoresrf

bestparamsrf.columns = ['Criterion', 'Max Depth', 'Subject', 'Score']
bestparamsrf = bestparamsrf[['Subject', 'Score', 'Criterion', 'Max Depth']]
summaryrf = bestparamsrf

# plot
fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
ax.bar(topics,scoresrf)
ax.set_ylabel('Score')
ax.set_xlabel('Variable Group')
ax.set_title('Random Forest Scores')
ax.set_xticklabels(labels = topics, rotation = 80)
ax.set_ylim(bottom = 0.5, top = 1)
plt.show()
plt.savefig("randomforestgraph.png")


bestparamslistada = []
scoresada = []
# Adaboost!
for fn in subset_fns:
    sub_data, sub_features, sub_cont = fn(data, featureinfo)
    X_prepared, encoder, y_prep = fit_prepare(data = sub_data, labels = y, cont = sub_cont)

    model = AdaBoostClassifier(base_estimator = DecisionTreeClassifier(),
                    n_estimators=100, random_state=0)

    params = {'base_estimator__criterion' : ('gini', 'entropy'), 
              'base_estimator__max_depth' : [1, 3, 5]}
    tuner = GridSearchCV(estimator = model, param_grid = params)
    tuner.fit(X_prepared, y_prep)

    bestparamslistada.append(tuner.best_params_)
    scoresada.append(tuner.best_score_)

# pandas df for best parameters
bestparamsada = pd.DataFrame(bestparamslistada)
bestparamsada['Subject'] = topics
bestparamsada['Score'] = scoresada

bestparamsada.columns = ['Tree Criterion', 'Tree Max Depth', 'Subject', 'Score']
bestparamsada = bestparamsada[['Subject', 'Score', 'Tree Criterion', 'Tree Max Depth']]

summaryada = bestparamsada


# plot
fig = plt.figure(figsize=(10,5))
ax = fig.add_axes([0,0,1,1])
ax.bar(topics,scoresada)
ax.set_ylabel('Score')
ax.set_xlabel('Variable Group')
ax.set_title('Random Forest Scores')
ax.set_xticklabels(labels = topics, rotation = 80)
ax.set_ylim(bottom = 0.5, top = 1)
plt.show()
plt.savefig('adaboostgraph.png')


# plot with both

N = len(topics)
ind = np.arange(N)
width = 0.4 

fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
ax.bar(ind, scoresrf, width, label='Random Forest')
ax.bar(ind + width, scoresada, width, label='AdaBoost')
ax.set_ylabel('Score')
ax.set_xlabel('Variable Group')
ax.set_title('Prediction Scores for Non-Political Features')
plt.xticks(ind + width / 2, topics)
ax.set_xticklabels(labels = topics, rotation = 80)
ax.set_ylim(bottom = 0.5, top = 1)
plt.legend(loc='best')
plt.savefig('comparison.png')



## combining features???

# hcsci, race, social
hc_data, hc_features, hc_cont = subset_hcsci(data, featureinfo)
rc_data, rc_features, rc_cont = subset_race(data, featureinfo)
sc_data, sc_features, sc_cont = subset_social_financial(data, featureinfo)

comb_data = pd.concat([hc_data, rc_data, sc_data], axis = 1)
comb_cont = hc_cont + rc_cont + sc_cont

X_comb, encoder, y_comb = fit_prepare(data = comb_data, labels = y, cont = comb_cont)

modelrf = RandomForestClassifier()
paramsrf = {'criterion' : ('gini', 'entropy'), 
               'max_depth': [1, 3, 10, 20]}
tunerrf = GridSearchCV(estimator = model, param_grid = params)
tunerrf.fit(X_comb, y_comb)

modelada = AdaBoostClassifier(base_estimator = DecisionTreeClassifier(),
                    n_estimators=100, random_state=0)

paramsada = {'base_estimator__criterion' : ('gini', 'entropy'), 
            'base_estimator__max_depth' : [1, 3, 5]}
tunerada = GridSearchCV(estimator = model, param_grid = params)
tunerada.fit(X_comb, y_comb)

summaryrf.to_latex(index = False)
summaryada.to_latex(index = False)