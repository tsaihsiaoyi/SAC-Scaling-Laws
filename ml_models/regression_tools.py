# -*- coding: utf-8 -*-
"""
Created on Sat Apr 13 21:09:01 2019

@author: Yifan Wang (wangyf@udel.edu)
"""

'''
Utility functions to make regression plots
'''

import os
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import norm
import seaborn as sns
#matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
import matplotlib.pyplot as plt 




'''
Plot the regression results
'''
      
def predict_y(x, intercept, J_nonzero):
    
    y = np.dot(x, J_nonzero) + intercept
    return y


def cal_path(alphas, model, X_cv_train, y_cv_train, X_cv_test, y_cv_test, fit_int_flag):
    
    '''
    Calculate both RMSE and number of coefficients path for plotting purpose
    '''
    
    RMSE_path = []
    coef_path = []
    
    for j in range(len(X_cv_train)):
        
        test_scores = np.zeros(len(alphas))
        coefs_i = np.zeros(len(alphas))
                
        for i, ai in enumerate(alphas):
            
            estimator = model(alpha = ai,  max_iter = 1e7, tol = 0.001, fit_intercept=fit_int_flag, random_state = 0)
            estimator.fit(X_cv_train[j], y_cv_train[j])
            # Access the errors, error per cluster
            test_scores[i] = np.sqrt(mean_squared_error(y_cv_test[j], estimator.predict(X_cv_test[j]))) #RMSE
            coefs_i[i] = len(np.nonzero(estimator.coef_)[0])
        
        RMSE_path.append(test_scores)
        coef_path.append(coefs_i)
    
    RMSE_path = np.transpose(np.array(RMSE_path))
    coef_path = np.transpose(np.array(coef_path))

    
    return RMSE_path, coef_path



def plot_coef_path(alpha, alphas, coef_path, model_name, output_dir = os.getcwd()):
    '''
    #plot alphas vs the number of nonzero coefficents along the path
    '''


    fig = plt.figure(figsize=(6, 6))
    
    plt.plot(-np.log10(alphas), coef_path, ':', linewidth= 0.8)
    plt.plot(-np.log10(alphas), np.mean(coef_path, axis = 1), 
             label='Average across the folds', linewidth=2)     
    plt.axvline(-np.log10(alpha), linestyle='--' , color='r', linewidth=3,
                label='Optimal alpha') 
    plt.legend(frameon=False, loc='best')
    plt.xlabel(r'$-log10(\lambda)$')
    plt.ylabel("Number of Nonzero Coefficients ")    
    plt.tight_layout()

    fig.savefig(os.path.join(output_dir, model_name + '_a_vs_n.png'))


def plot_RMSE_path(alpha, alphas, RMSE_path, model_name, output_dir = os.getcwd()):
        
    '''
    #plot alphas vs RMSE along the path
    '''

    fig = plt.figure(figsize=(6, 6))
    
    plt.plot(-np.log10(alphas), RMSE_path, ':', linewidth= 0.8)
    plt.plot(-np.log10(alphas), np.mean(RMSE_path, axis = 1), 
             label='Average across the folds', linewidth=2)  
    plt.axvline(-np.log10(alpha), linestyle='--' , color='r', linewidth=3,
                label='Optimal alpha') 
    
    plt.legend(frameon=False,loc='best')
    plt.xlabel(r'$-log10(\lambda)$')
    plt.ylabel("RMSE (eV)")    
    plt.tight_layout()
   
    fig.savefig(os.path.join(output_dir, model_name  + '_a_vs_cv.png'))

       
def plot_path(X, y, alpha, alphas, RMSE_path, coef_path, model, model_name, output_dir = os.getcwd()):
    
    '''
    Overall plot function for lasso/elastic net
    '''
    
    plot_coef_path(alpha, alphas, coef_path, model_name, output_dir)
    plot_RMSE_path(alpha, alphas, RMSE_path, model_name, output_dir)
    
    '''
    #make performance plot - optional
    '''
    #plot_performance(X, y, model, model_name, output_dir)
    


def plot_ridge_path(alpha, alphas, RMSE_path, model_name, output_dir = os.getcwd()):
    
    fig = plt.figure(figsize=(6, 6))
    
    plt.plot(-np.log10(alphas), np.mean(RMSE_path, axis = 1), 
             label='Average across the folds', linewidth=2)  
    plt.axvline(-np.log10(alpha), linestyle='--' , color='r', linewidth=3,
                label='Optimal alpha') 
    
    plt.legend(frameon=False,loc='best')
    plt.xlabel(r'$-log10(\lambda)$')
    plt.ylabel("RMSE (eV)")    
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, model_name +'_a_vs_cv.png'))

    
    
def plot_performance(X, y, model, model_name, output_dir = os.getcwd()): 
    
    '''
    #plot parity plot
    '''
    y_predict_all = model.predict(X)
    #y_predict_all = predict_y(pi_nonzero, intercept, J_nonzero)
    
    plt.figure(figsize=(6,6))
    
    fig, ax = plt.subplots()
    ax.scatter(y, y_predict_all, s=60, facecolors='none', edgecolors='r')
    
    plt.xlabel("DFT Cluster Energy (eV)")
    plt.ylabel("Predicted Cluster Energy (eV)")
    
    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
        np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
    ]
    
    #  plot both limits against eachother
    ax.plot(lims, lims, 'k--', alpha=0.75, zorder=0)
    ax.set_xlim(lims)
    ax.set_ylim(lims)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, model_name + '_parity.png'))
    
    '''
    #plot error plot
    '''

    plt.figure(figsize=(6,6))
    
    fig, ax = plt.subplots()
    ax.scatter(y,y_predict_all - y, s = 20, color ='r')
    
    plt.xlabel("DFT Cluster Energy (eV)")
    plt.ylabel("Error Energy (eV)")
    
    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
        np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
    ]
    
    #  plot both limits against eachother
    ax.plot(lims, np.zeros(len(lims)), 'k--', alpha=0.75, zorder=0)
    ax.set_xlim(lims)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, model_name +'_error.png'))
    
    '''
    #plot error plot per atom
    '''

    plt.figure(figsize=(6,6))
    
    fig, ax = plt.subplots()
    ax.scatter(y, (y_predict_all - y), s=20, color = 'r')
    
    plt.xlabel("DFT Cluster Energy (eV)")
    plt.ylabel("Error Energy per atom (eV)")
    
    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
        np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
    ]
    
    #  plot both limits against eachother
    ax.plot(lims, np.zeros(len(lims)), 'k--', alpha=0.75, zorder=0)
    ax.set_xlim(lims)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, model_name + '_error_atom.png'))

def cal_performance(X, y, model): 
    
    y_predict_all = model.predict(X)
    RMSE = np.sqrt(mean_squared_error(y, y_predict_all))
    r2 = r2_score(y, y_predict_all)
    
    return RMSE, r2
    
def parity_plot(yobj, ypred, model_name,  output_dir, test_RMSE):
    '''
    Plot the parity plot of y vs ypred
    return R2 score and MSE for the model for the whole dataset
    colorcode different site types
    '''
    sns.set_style("ticks")
    all_RMSE = np.sqrt(np.mean((yobj - ypred)**2))
    r2 = r2_score(yobj, ypred)
    fig, ax = plt.subplots(figsize=(6, 6))

    ax.scatter(yobj,
                ypred,
                alpha = 0.5,
                s  = 60)
    ax.plot([yobj.min(), yobj.max()], [yobj.min(), yobj.max()], 'k--', lw=2)
    
    ax.set_xlabel('DFT-Calculated ')
    ax.set_ylabel('Model Prediction')
    plt.title(r'RMSE={:.2}, $R^2$ ={:.2}'.format(test_RMSE, r2))
    plt.legend(bbox_to_anchor = (1.02, 1),loc= 'upper left', frameon=False)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, model_name + '_parity.png'))
    
    return all_RMSE, r2    

def error_distribution(yobj, ypred, model_name, output_dir):
    
    '''
    Plot the error distribution
    return the standard deviation of the error distribution
    '''
    fig, ax = plt.subplots(figsize=(6,6))
    ax.hist(yobj - ypred,density=1, alpha=0.5, color='steelblue')
    mu = 0
    sigma = np.std(yobj - ypred)
    x_resid = np.linspace(mu - 3*sigma, mu + 3*sigma, 100)
    ax.plot(x_resid,norm.pdf(x_resid, mu, sigma), color='r')
    plt.title(r'{}, $\sigma$-{:.2}'.format(model_name, sigma))
    fig.savefig(os.path.join(output_dir, model_name + '_parity.png'))

    return sigma

def plot_coef(coefs, model_name,  output_dir, terms = None):
    
    if terms == None:  terms = [str(i) for i in range(0,len(coefs))]
    
    xi = np.arange(len(coefs))*2
    fig, ax = plt.subplots(figsize=(6,6))
    plt.bar(xi, coefs)
    linex = np.arange(xi.min()-1, xi.max()+2)
    plt.plot(linex, linex*0, c = 'k')
    plt.xticks(xi, terms, rotation=45)
    plt.ylabel("Regression Coefficient Value (eV)")
    plt.xlabel("Regression Coefficient")  
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, model_name + '_coef_distribution.png'))
    
#%% Plot coefficients function
def make_coef_matrix(x_features, Js, n_features, x_secondary_feature_names):
    
    '''
    Put the coefficient matrix back
    '''
    
    coef_matrix = np.zeros((n_features, n_features))
    
    for xi, feature_names in enumerate(x_features):
    
        Ji = Js[xi]
        
        if len(feature_names) == 1:
            
            if feature_names == '1':
                coef_matrix[0,0] = Ji
                
            else:
                # row number
                ri = np.where(np.array(x_secondary_feature_names) == feature_names)[0][0] + 1
                # column number
                ci = 0
                coef_matrix[ri,ci] = Ji
                
        if len(feature_names) == 2:
            # row number
            ri = np.where(np.array(x_secondary_feature_names) == feature_names[1])[0][0] + 1
            ci = np.where(np.array(x_secondary_feature_names) == feature_names[0])[0][0] + 1
            
            coef_matrix[ri, ci] = Ji
            
    return coef_matrix


def plot_tri_correlation_matrix(coef_matrix, output_dir, x_plot_feature_names, model_name):
    
    '''
    Plot the correlation matrix in a lower trianglar fashion
    '''
    corr = coef_matrix.copy()
    
    # create mask, true for white, false to show the value
    mask = np.zeros_like(corr)
    mask[np.triu_indices_from(mask)] = True
    mask[0,0] = False
    mask[2,1] = True
    mask[4,3] = True
    mask[6,5] = True
    mask[9,8] = True
    mask[11,10] = True
    mask[13,12] = True
    
    #new masks
    mask[4,1] = True
    mask[3,2] = True
    mask[6,1] = True
    mask[5,2] = True
    mask[6,3] = True
    mask[5,4] = True
    
    mask[11,8] = True
    mask[13,8] = True
    mask[10,9] = True
    mask[12,9] = True
    mask[12,11] = True
    mask[13,10] = True
    
    
    # Set up the matplotlib figure
    fig, ax = plt.subplots(figsize=(12, 12))
    # Generate a custom diverging colormap
    cmap = sns.color_palette("RdBu_r", 7) 
    sns.set_style("white")
    sns.heatmap(corr, mask = mask, cmap=cmap, vmin = -0.5, vmax=0.5, center=0,
                square=True, linewidths=1.5, cbar_kws={"shrink": 0.7})
    for _, spine in ax.spines.items():
        spine.set_visible(True)
    ax.tick_params('both', length=0, width=0, which='major')
    ax.set_xticks(np.arange(0,len(x_plot_feature_names))+0.5)
    ax.set_xticklabels(x_plot_feature_names, rotation = 45)
    ax.set_yticks(np.arange(0,len(x_plot_feature_names))+0.5)
    ax.set_yticklabels(x_plot_feature_names, rotation = 0)
    ax.set_xlabel('Descriptor 1')
    ax.set_ylabel('Descriptor 2')
    fig.savefig(os.path.join(output_dir, model_name + '_coef_heatmap.png'))