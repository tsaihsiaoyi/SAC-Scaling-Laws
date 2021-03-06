# %% [markdown]
# ## Training the Single Atom Binding Energy Correlation in Python
# 
# Author: Yifan Wang [(wangyf@udel.edu)](wangyf@udel.edu)
# 
# Predict $E_{bind}$ of single-atom metal on support based on descriptors (features) 'Ebulk', 'Evac', 'delta X' , 'CN', 'bond angle' (values from DFT calculations)
# 
# The form of the scaling law is obtained from various supervised machine learning (ML) methods and the traing procedure is shown below. The ML methods used include:
# 
# - [LASSO regression](#LASSO) 
# 
# - [Ridge regression](#ridge)
# 
# - [Elastic net](#enet)
# 
# - [Ordinary Least Square (OLS) regression](#OLS)
# 
# The LASSO model is selected based on the lowest testing RMSE
# 

# %%
#%% Import all necessary libraries 
import os

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm

import numpy as np

import pandas as pd
import seaborn as sns
from scipy.stats import norm
from sklearn import linear_model
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA

from sklearn.linear_model import (ElasticNet, ElasticNetCV, Lasso, LassoCV,
                                  Ridge, RidgeCV, enet_path, lasso_path)
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import (LeaveOneOut, RepeatedKFold,
                                     cross_val_score, train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

import regression_tools as rtools

font = {'size'   : 20}

matplotlib.rc('font', **font)
matplotlib.rcParams['axes.linewidth'] = 1.5
matplotlib.rcParams['xtick.major.size'] = 12
matplotlib.rcParams['xtick.labelsize'] = 16
matplotlib.rcParams['ytick.labelsize'] = 16
matplotlib.rcParams['xtick.major.width'] = 3
matplotlib.rcParams['ytick.major.size'] = 12
matplotlib.rcParams['ytick.major.width'] = 3
matplotlib.rcParams['legend.fontsize'] = 16
matplotlib.rcParams['figure.dpi'] = 300. # set plotting resolution

# %% [markdown]
# ### Step 1 - Import Data 

# %%
#%% read adsoprtion energy and barder charge from a csv file

data = pd.read_csv('Ea_data.csv', header = 0)
metal = np.array(data['metal'])
support = np.array(data['support'])
descriptors  = ['Ec', 'Evac', 'delta X' , 'CN', 'angle']

Ebind = np.array(data['Ebind'])

# load the physical descriptor values 
Ec = np.array(data['Ec'])
Evac = np.array(data['Evac'])
deltaX = np.array(data['delta X'])
CN = np.array(data['CN'], dtype = float)
angle = np.array(data['angle'], dtype = float)

# %% [markdown]
# ### Step 2 - Generate the descriptors (features)

# %%
#%% Prepare for the features based on the original data

# Numerical orders
orders = [1, -1, 0.5, -0.5, 2, -2]


def transformers(xv, orders):

    '''
    Transform each column of primary featurs into secondary features
    '''
    x_features = np.reshape(xv, (len(xv),1))
    
    for oi in orders[1:]:
        x_features = np.concatenate((x_features, np.reshape(xv, (len(xv),1))**oi), axis = 1)
    
    '''
    Add additional features
    '''
    x_features = np.concatenate((x_features, np.log(np.reshape(xv, (len(xv),1)))), axis = 1)
    
    return x_features
'''
Get the names and orders
'''    
# primary and secondary feature names
x_primary_feature_names = descriptors.copy()
x_secondary_feature_names_2d = []
orders_log = orders + ['ln']

# The number for all numerical opeators 
all_orders_log = []

for xi in x_primary_feature_names:  
    x_secondary_feature_names_2d.append([xi + '_' + str(oi) for oi in orders_log])
    all_orders_log += orders_log
    
x_secondary_feature_names = []
for xi in x_secondary_feature_names_2d:
    x_secondary_feature_names += xi


'''
Transform the primary features into the secondary features
''' 
Ec_features = transformers(Ec, orders)    
Evac_features = transformers(Evac, orders)   
deltaX_features = transformers(deltaX, orders)    
CN_features = transformers(CN, orders)   
angle_features = transformers(angle, orders)   

# Combine all features
X_init = np.concatenate((Ec_features, Evac_features, deltaX_features, CN_features,angle_features ),axis = 1) 


poly = PolynomialFeatures(2, interaction_only=True)
X_poly = poly.fit_transform(X_init)
orders_m = poly.powers_

# %% [markdown]
# ### Step 3 - Scaling the features to zero mean and unit variance
# 

# %%
#%% Process X and y, scale

X_before_scaling = X_poly.copy()
y = Ebind
scaler = StandardScaler().fit(X_before_scaling[:,1:])

sv = scaler.scale_
mv = scaler.mean_

X = X_before_scaling.copy()
X[:,1:] = scaler.transform(X_before_scaling[:,1:])


fit_int_flag = False # Not fitting for intercept, as the first coefficient is the intercept

# %% [markdown]
# ### Step 4 - Set the cross-validation scheme
# 

# %%
#%% Cross validation setting

# Set random state here
random_state = 0
# Train test split, save 20% of data point to the test set
X_train, X_test, y_train, y_test, X_before_train, X_before_test = train_test_split(X, y, X_before_scaling, test_size=0.2, random_state = random_state)
                    
                    
# The alpha grid used for plotting path
alphas_grid = np.logspace(0, -3, 20)

# Cross-validation scheme                                  
rkf = RepeatedKFold(n_splits = 10, n_repeats = 10 , random_state =rs)


# Explicitly take out the train/test set
X_cv_train, y_cv_train, X_cv_test, y_cv_test = [],[],[],[]

for train_index, test_index in rkf.split(X_train):
    X_cv_train.append(X_train[train_index])
    y_cv_train.append(y_train[train_index])
    X_cv_test.append(X_train[test_index])
    y_cv_test.append(y_train[test_index])

# %% [markdown]
# ### Step 5 - Train ML models
# %% [markdown]
# #### LASSO Regression<a name="lasso"></a>
# 

# %%
#%% LASSO regression
'''   
# LassoCV to obtain the best alpha, the proper training of Lasso
'''
model_name = 'lasso_Ebind'
base_dir = os.getcwd()
output_dir = os.path.join(base_dir, model_name)
if not os.path.exists(output_dir): os.makedirs(output_dir)    

lasso_cv  = LassoCV(cv = rkf,  max_iter = 1e7, tol = 0.001, fit_intercept=fit_int_flag, random_state=random_state)
lasso_cv.fit(X_train, y_train)

# the optimal alpha from lassocv
lasso_alpha = lasso_cv.alpha_
# Coefficients for each term
lasso_coefs = lasso_cv.coef_
# The original intercepts 
lasso_intercept = lasso_cv.intercept_

# Access the errors 
y_predict_test = lasso_cv.predict(X_test)
y_predict_train = lasso_cv.predict(X_train)


lasso_RMSE_test = np.sqrt(mean_squared_error(y_test, y_predict_test))
lasso_RMSE_train = np.sqrt(mean_squared_error(y_train, y_predict_train))
lasso_r2_train = r2_score(y_train, y_predict_train)


##Use alpha grid prepare for lassopath
lasso_RMSE_path, lasso_coef_path = rtools.cal_path(alphas_grid, Lasso, X_cv_train, y_cv_train, X_cv_test, y_cv_test, fit_int_flag)
rtools.plot_path(X, y, lasso_alpha, alphas_grid, lasso_RMSE_path, lasso_coef_path, lasso_cv, model_name, output_dir)
# Plot parity plot
lasso_RMSE, lasso_r2 = rtools.parity_plot(y, lasso_cv.predict(X), model_name, output_dir, lasso_RMSE_test)


# The indices for non-zero coefficients/significant cluster interactions 
J_index = np.nonzero(lasso_coefs)[0]
# The number of non-zero coefficients/significant cluster interactions  
n_nonzero = len(J_index)
# The values of non-zero coefficients/significant cluster interactions  
J_nonzero = lasso_coefs[J_index] 


'''
Convert the coefficient to unnormalized form
'''
lasso_coefs_unnormailized = np.zeros_like(lasso_coefs)
lasso_coefs_unnormailized[1:] = lasso_coefs[1:]/sv
lasso_coefs_unnormailized[0] = lasso_coefs[0] - np.sum(mv/sv*lasso_coefs[1:])

# %% [markdown]
# #### Ridge regression<a name="ridge"></a>
# 

# %%
#%% Ridge regression
'''
# Ridge regression
'''
'''
# RidgeCV to obtain the best alpha, the proper training of ridge
'''
model_name = 'ridge_Ebind'
output_dir = os.path.join(base_dir, model_name)
if not os.path.exists(output_dir): os.makedirs(output_dir)    

alphas_grid_ridge = np.logspace(0, -3, 20)
ridgeCV = RidgeCV(alphas = alphas_grid_ridge,  cv = rkf, fit_intercept=fit_int_flag)
ridgeCV.fit(X_train, y_train)
ridge_alpha = ridgeCV.alpha_ 
ridge_intercept = ridgeCV.intercept_ 
ridge_coefs = ridgeCV.coef_

# Access the errors 
y_predict_test = ridgeCV.predict(X_test)
y_predict_train = ridgeCV.predict(X_train)

ridge_RMSE_test = np.sqrt(mean_squared_error(y_test, y_predict_test))
ridge_RMSE_train = np.sqrt(mean_squared_error(y_train, y_predict_train))
ridge_r2_train = r2_score(y_train, y_predict_train)   

# plot the rigde path
ridge_RMSE_path, ridge_coef_path = rtools.cal_path(alphas_grid_ridge, Ridge, X_cv_train, y_cv_train, X_cv_test, y_cv_test, fit_int_flag)
rtools.plot_RMSE_path(ridge_alpha, alphas_grid_ridge, ridge_RMSE_path, model_name, output_dir)
# plot the parity plot
ridge_RMSE, ridge_r2 = rtools.parity_plot(y, ridgeCV.predict(X), model_name, output_dir, ridge_RMSE_test)

# Unnormalized coefficients
ridge_coefs_unnormailized = np.zeros_like(ridge_coefs)
ridge_coefs_unnormailized[1:] = ridge_coefs[1:]/sv
ridge_coefs_unnormailized[0] = ridge_coefs[0] - np.sum(mv/sv*lasso_coefs[1:])


# %% [markdown]
# #### Elastic net<a name="enet"></a>
# 
# The L1 ratio is varied and the best model is selected based on testing RMSE

# %%
#%% elastic net results
model_name = 'enet_Ebind'
output_dir = os.path.join(base_dir, model_name)
if not os.path.exists(output_dir): os.makedirs(output_dir)    

def l1_enet(ratio):
    
    '''
    input l1 ratio and return the model, non zero coefficients and cv scores
    training elastic net properly
    '''
    enet_cv  = ElasticNetCV(cv = rkf, l1_ratio=ratio,  max_iter = 1e7, tol = 0.001, fit_intercept=fit_int_flag, random_state= rs)
    enet_cv.fit(X_train, y_train)
    
    # the optimal alpha
    enet_alpha = enet_cv.alpha_
    enet_coefs = enet_cv.coef_
    n_nonzero = len(np.where(abs(enet_coefs)>=1e-7)[0])
    # Access the errors 
    y_predict_test = enet_cv.predict(X_test)
    y_predict_train = enet_cv.predict(X_train)
    
    # error per cluster
    enet_RMSE_test = np.sqrt(mean_squared_error(y_test, y_predict_test))
    enet_RMSE_train = np.sqrt(mean_squared_error(y_train, y_predict_train))


    return enet_cv, enet_alpha, n_nonzero, enet_RMSE_test, enet_RMSE_train

'''
# Tune the l1 ratio by a grid search from 0 to 1
'''

# The vector of l1 ratio
l1s = [0.01, 0.05]
l1s = l1s + list(np.around(np.arange(0.1, 1.05, 0.05), decimals= 2))


enet = []
enet_alphas = []
enet_n  = []
enet_RMSE_test = []
enet_RMSE_train = []
enet_RMSE_test_atom = []
enet_RMSE_train_atom = []


print('Training Progress: \n')
for i, l1i in enumerate(l1s):
    # Report the training progress
    print('{:0.2f} % done'.format(100*(i+1)/len(l1s)))
    enet_cv, ai, n, RMSE_test, RMSE_train = l1_enet(l1i)
    
    enet.append(enet_cv)
    enet_alphas.append(ai)
    enet_n.append(n)
    
    enet_RMSE_test.append(RMSE_test)
    enet_RMSE_train.append(RMSE_train)

# Save elastic net results to csv
# expand the vector, put the result of ridge to the first
l1_ratio_v = np.array([0] + l1s)
enet_n_v  = np.array([X.shape[1]] + enet_n)
enet_RMSE_test_v = np.array([ridge_RMSE_test] + enet_RMSE_test)

enet_RMSE_test_v = [ridge_RMSE_test] + enet_RMSE_test
fdata = pd.DataFrame(np.transpose([l1_ratio_v, enet_n_v, enet_RMSE_test_v]), columns = ['l1 ratio', 'number of cluster', 'error per cluster (eV)'])
fdata.to_csv(os.path.join(output_dir, 'enet_data.csv'), index=False, index_label=False)

#%% Plot elastic net results
sns.set_style("ticks")
plt.figure(figsize=(8,6))
fig, ax1 = plt.subplots()
ax1.plot(l1_ratio_v, enet_RMSE_test_v, 'bo-')
ax1.set_xlabel('L1 Ratio')
# Make the y-axis label, ticks and tick labels match the line color.
ax1.set_ylabel('RMSE/cluster(ev)', color='b')
ax1.tick_params('y', colors='b')

ax2 = ax1.twinx()
ax2.plot(l1_ratio_v, enet_n_v, 'r--')
ax2.set_ylabel('# Nonzero Coefficients', color='r')
ax2.tick_params('y', colors='r')

fig.tight_layout()
fig.savefig(os.path.join(output_dir, 'elastic_net.png'))


# enet_path to get alphas and coef_path
'''
#Use alpha grid prepare for enet_path when RMSE is mininal 
'''
enet_RMSE_path, enet_coef_path = rtools.cal_path(alphas_grid, ElasticNet, X_cv_train, y_cv_train, X_cv_test, y_cv_test, fit_int_flag)    
enet_min_index = np.argmin(enet_RMSE_test)
l1s_min = l1s[enet_min_index] 
enet_min = enet[enet_min_index]
enet_min_RMSE_test = np.amin(enet_RMSE_test)
rtools.plot_path(X, y, enet_alphas[enet_min_index], alphas_grid, enet_RMSE_path, enet_coef_path, enet[enet_min_index], model_name, output_dir)


#%% Select the significant cluster interactions 

# the optimal alpha from lassocv
enet_min_alpha = enet_min.alpha_
# Coefficients for each term
enet_min_coefs = enet_min.coef_
# The original intercepts 
enet_min_intercept = enet_min.intercept_
enet_min_r2_train = r2_score(y_train, enet_min.predict(X_train))


# The indices for non-zero coefficients/significant cluster interactions 
J_index = np.nonzero(enet_min_coefs)[0]
# The number of non-zero coefficients/significant cluster interactions  
n_nonzero = len(J_index)
# The values of non-zero coefficients/significant cluster interactions  
J_nonzero = enet_min_coefs[J_index] 
# Plot the parity plot
enet_min_RMSE, enet_min_r2 = rtools.parity_plot(y, enet_min.predict(X), model_name, output_dir, enet_min_RMSE_test)

'''
Convert the coefficient to unnormalized form
'''
enet_min_coefs_unnormailized = np.zeros_like(enet_min_coefs)

enet_min_coefs_unnormailized[1:] = enet_min_coefs[1:]/sv
enet_min_coefs_unnormailized[0] = enet_min_coefs[0] - np.sum(mv/sv*enet_min_coefs[1:])

# %% [markdown]
# #### Ordinary least square (OLS) regression<a name="OLS"></a>

# %%
#%% Second order Least Square regression

model_name = 'OLS_Ebind'
output_dir = os.path.join(base_dir, model_name)
if not os.path.exists(output_dir): os.makedirs(output_dir)    

OLS = linear_model.LinearRegression(fit_intercept=fit_int_flag)
OLS.fit(X_train,y_train) 
OLS_coefs = OLS.coef_

# Access the errors 
y_predict_test = OLS.predict(X_test)
y_predict_train = OLS.predict(X_train)
OLS_r2_train = r2_score(y_train, y_predict_train)

OLS_RMSE_test = np.sqrt(mean_squared_error(y_test, y_predict_test))
OLS_RMSE_train = np.sqrt(mean_squared_error(y_train, y_predict_train))
# Plot the parity plot
OLS_RMSE, OLS_r2 = rtools.parity_plot(y, OLS.predict(X), model_name, output_dir, OLS_RMSE_test)

OLS_coefs_unnormailized = np.zeros_like(OLS_coefs)
OLS_coefs_unnormailized[1:] = OLS_coefs[1:]/sv
OLS_coefs_unnormailized[0] = OLS_coefs[0] - np.sum(mv/sv*OLS_coefs[1:])

# %% [markdown]
# #### Evaluate the performance of LASSO model 

# %%
#%% LASSO model performance
'''
Based on metal
'''

metal_types = np.unique(metal)
types = metal_types.copy()
category = metal.copy()

fig, ax = plt.subplots(figsize=(6, 6))
color_set = cm.jet(np.linspace(0,1,len(types)))
for type_i, ci in zip(types, color_set):
    indices = np.where(np.array(category) == type_i)[0]
    ax.scatter(y[indices],
                    lasso_cv.predict(X)[indices],
                    label=type_i,
                    facecolor = ci, 
                    alpha = 0.8,
                    s  = 100)
ax.plot([y.min(), y.max()], [y.min(), y.max()], 'k--',  lw=2)
ax.set_xlabel('DFT-Calculated $E_{bind}$ (eV) ')
ax.set_ylabel('Model Prediction $E_{bind}$ (eV)')
plt.legend(bbox_to_anchor = (1.02, 1),loc= 'upper left', frameon=False)
plt.text(3, 1, '$RMSE_{test}$ = ' + str(np.around(lasso_RMSE_test, decimals = 3)))
plt.text(4,0.4, '$R^2$ = ' + str(np.around(lasso_r2, decimals = 3)) )



'''
Based on support
'''
support_types = np.unique(support)
types = support_types.copy()
category = support.copy()

fig, ax = plt.subplots(figsize=(6, 6))
color_set = cm.jet(np.linspace(0,1,len(types)))
for type_i, ci in zip(types, color_set):
    indices = np.where(np.array(category) == type_i)[0]
    ax.scatter(y[indices],
                    lasso_cv.predict(X)[indices],
                    label=type_i,
                    facecolor = ci, 
                    alpha = 0.8,
                    s  = 100)
ax.plot([y.min(), y.max()], [y.min(), y.max()], 'k--',  lw=2)
ax.set_xlabel('DFT-Calculated $E_{bind}$ (eV) ')
ax.set_ylabel('Model Prediction $E_{bind}$ (eV)')
plt.legend(bbox_to_anchor = (1.02, 1),loc= 'upper left', frameon=False)
plt.text(3, 1, '$RMSE_{test}$ = ' + str(np.around(lasso_RMSE_test, decimals = 3)))
plt.text(4,0.4, '$R^2$ = ' + str(np.around(lasso_r2, decimals = 3)) )

