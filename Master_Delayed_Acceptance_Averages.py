'''
Implementation of weighted delayed acceptance sampling algorithm for the double-glazing inverse problem. Referece paper: "Markov Chain Monte Carlo Using 
an Approximation" by J. Andrés Christen and Colin Fox. Uses spatial averaging variation of the likelihood function.
'''

from fenics import *
import numpy as np

from Master_Solver import master_solver
from Stretch_Mesh import stretch_mesh
from Time_Stepping import time_organiser

def log_ratio(#y,
              #u1,
              #u2,
              alpha1,
              alpha2,
              sigma_p,
              sigma_l,
              mu_p,
              f1_norm,
              f2_norm
              ):
    '''
    Calculate the log acceptance ratio between mesh point values using L2 norm.

    Inputs:
        alpha1:         Float:      First alpha value for comparison.
        alpha2:         Float:      Second alpha value for comaprison.
        sigma_p:        Float:      Variance of Gaussian prior density.
        sigma_l:        Float:      Variance used in likelihood function.
        mu_p:           Float:      Mean of Gaussian prior density.
        f1_norm:        Float:      L2 norm between data and solution generated with alpha1.
        f2_norm:        Float:      L2 norm between data and solution generated with alpha2.
    Outputs:
        log_ratio:      Float:      Natural log of ratio of likelihoods, used in acceptance.
    '''
    log_ratio = 0.5 * ((((alpha1 - mu_p) ** 2 - (alpha2 - mu_p) ** 2) / sigma_p ** 2) + (f1_norm ** 2 - f2_norm ** 2)/ sigma_l ** 2)
    
    return log_ratio

def A_mat(u):
    '''
    Format u into correct shape.
    '''
    return u

def A_mat_coarse(u):
    '''
    Format u into correct shape (coarse edition).
    '''
    return u

def delayed_acceptance(alpha0,
                       y,
                       y_coarse,
                       coarsening,
                       sigma_q, 
                       sigma_p,
                       sigma_l,
                       mu_p,
                       nx,
                       tau,
                       epsilon,
                       iterations,
                       burnin,
                       num_steps,
                       num_steps_coarse,
                       dt_min,
                       dt_max,
                       reg
                       ):
    '''
    Carries out iterations of the delayed acceptance algorithm using an approximation of the likelihood. Based on RWMH, this algorithm aims to 
    decrease the sampling time by first using a cheaper-to-compute approximation of the likelihood, and only computing the full likelihood 
    after acceptance.

    Inputs:
        alpha0:         Float:      Initial value for alpha.
        y:              np.Array:   Generated data encoding information about heat distribution in time.
        y_coarse:       np.Array:   y projected onto coarser grid.
        coarsening:     Int:        Size of coarse grid (square).
        sigma_q:        Float:      Variance of proposal distribution (stepsize).
        sigma_p:        Float:      Variance of prior distribution. 
        sigma_l:        Float:      Variance in likelihood (estimate of the noise in the data).
        mu_p:           Float:      Mean of prior distribution.
        nx:             Int:        Size of fine mesh (must be square, nx=ny).
        tau:            Float:      Rate of growth of hot wall boundary.
        epsilon:        Float:      Diffusion coefficient from advection-diffusion equation.
        iterations:     Int:        Desired number of iterations for delayed acceptance algorithm.
        burnin:         Int:        Desired number of burn-in iterations.
        num_steps:      Int:        Number of steps in time calculated by the double-glazing solver.
        dt_min:         Float:      Initial timestepping value (variable time-stepping).
        dt_max:         Float:      Limit of dt (variable time-stepping).
        reg:            Float:      Regularisation constant used in variable time-stepping (hyperparameter).
    Outputs:
        alpha_list:     List:       List of samples for alpha generated by delayed acceptance algorithm.
    '''

    # Generate meshes using Stretch_Mesh.py.
    mesh = stretch_mesh(nx=nx, ny=nx)
    mesh_coarse = stretch_mesh(nx=coarsening, ny=coarsening)
    
    # Initialise alpha1 and alpha_list.
    alpha_list = [alpha0]
    alpha1 = alpha0

    # Initialise acceptance ratio list.
    A_list = []

    ### TESTING ###
    # likelihood_list = []
    # likelihood_coarse_list = []

    # Generate numerical solution for inital alpha1 value (high resolution).
    u1, __ = master_solver(mesh,
                           tau,
                           alpha1,
                           epsilon,
                           num_steps,
                           dt_min,
                           dt_max,
                           reg
                           )
    # Generate numerical solution for inital alpha1 value (low resolution).
    u1_coarse, __ = master_solver(mesh_coarse,
                                  tau,
                                  alpha1,
                                  epsilon,
                                  num_steps_coarse,
                                  dt_min,
                                  dt_max,
                                  reg
                                  )

    # Take means over spatial domain.
    u1 = np.mean(u1, axis=1)
    u1_coarse = np.mean(u1_coarse, axis=1)

    # Calculate norms between generated solutions and the data (both high and low resolutions).
    u1_norm = np.linalg.norm(y - A_mat(u1))
    u1_coarse_norm = np.linalg.norm(y_coarse - A_mat(u1_coarse))

    # Initialise accept-reject ratio list:
    accept = 0
    reject = 0
    ratio_list = []

    # Initialise inital rejection list:
    reject_first = 0
    reject_first_list = []

    # Begin Delayed Acceptance interations.
    for i in range(iterations):
        
        # Propose next sample.
        alpha2 = np.random.normal(alpha1, sigma_q)

        # Generate numerical solution for alpha2 (low resolution).
        u2_coarse, __ = master_solver(mesh_coarse,
                                      tau,
                                      alpha2,
                                      epsilon,
                                      num_steps_coarse,
                                      dt_min,
                                      dt_max,
                                      reg
                                      )

        # Take mean over spatial domain.
        u2_coarse = np.mean(u2_coarse, axis=1)

        # Caluclate norm between generated solution and the data (low resolution).
        u2_coarse_norm = np.linalg.norm(y_coarse - A_mat_coarse(u2_coarse))

        # Calculate log of acceptance ratio (low resolution).
        A_coarse = log_ratio(#y,
                             #u1,
                             #u2,
                             alpha1,
                             alpha2,
                             sigma_p,
                             sigma_l,
                             mu_p,
                             u1_coarse_norm,
                             u2_coarse_norm
                             )

        # Inital acceptance step. Upon acceptance, repeat for high resolution data.
        if A_coarse >= 0 or np.log(np.random.uniform(0,1)) <= A_coarse:
            
            # Generate numerical solution for alpha2 (high resolution).
            u2, __ = master_solver(mesh,
                                   tau,
                                   alpha2,
                                   epsilon,
                                   num_steps,
                                   dt_min,
                                   dt_max,
                                   reg
                                   )

            # Take mean in spatial dimension.
            u2 = np.mean(u2, axis=1)

            # Caluclate norm between generated solution and the data (low resolution).
            u2_norm = np.linalg.norm(y - A_mat(u2))

            # Calculate log of accpetance ratio (high resolution).
            A = log_ratio(#y,
                          #u1,
                          #u2,
                          alpha1,
                          alpha2,
                          sigma_p,
                          sigma_l,
                          mu_p,
                          u1_norm,
                          u2_norm
                          )
            
            A_list.append(A.copy())
            
            # Secondary acceptance step.
            if A >= 0 or np.log(np.random.uniform(0,1)) <= A + min(0, A_coarse):  ############################# THINK ABOUT THIS!!!!!! ######################################
                
                # Accept proposal as next sample.
                alpha1 = alpha2

                # Reassign variables accordingly.
                u1 = u2
                u1_coarse = u2_coarse
                u1_norm = u2_norm
                u1_coarse_norm = u2_coarse_norm

                # Count number of acceptances for accept-reject ratio.
                accept += 1

                ### TESTING ###
                # likelihood_list.append(u2_norm)
                # likelihood_coarse_list.append(u2_coarse_norm)
            
            else:
                # Count number of rejections for accept-reject ratio.
                reject += 1
                print('rejected second')
        else:
            # Count number of rejections for accept-reject ratio.
            reject += 1
            # Count number of initial rejections.
            reject_first += 1
            
            print('rejected first')

        # Once burn-in iterations are complete...
        if i >= burnin:

            # ...add sample to list.
            alpha_list.append(alpha1)

            # Add ratio to accept-reject ratio list.
            if reject == 0 and accept != 0:
                ratio_list.append(1)
            else:
                ratio_list.append(accept/reject)

            # Add initial rejections to list.
            reject_first_list.append(reject_first)

        # Sanity check.
        print(i)

    return(alpha_list,
           A_list,
           ratio_list,
           reject_first_list
           # likelihood_list,
           # likelihood_coarse_list
           )


if __name__ == "__main__":

    import pickle 

    def main():

        # Solver parameters.
        alpha0 = 2                              # Initial guess for alpha.
        tau = 1/10                              # Rate of growth of hot wall.
        epsilon = 1/100                         # Diffusion coefficient.
        num_steps = 60                          # Number of steps to run solver for.
        nx = 32                                 # Number of horizontal grid points on mesh (ny = nx).
        
        # Variable time-stepping variables.                                                                                                          
        dt_min = 1e-3                           # Inital value for dt.
        dt_max = 0.1                            # Limit of dt values as t appraches infty.
        reg = 10                                # Regularisation constant.

        # RWMH parameters.
        iterations = 10                       # Number of samples to generate (-burnin).
        burnin = 0                              # Number of burn-in iterations.
        sigma_q = 0.5                           # Vairance of normal proposal distribution.
        sigma_p = 1                             # Variance of normal prior.
        mu_p = 0                                # Mean of normal prior.
        sigma_l = 0.2                           # Variance in likelihood (estimate of noise in data):

        # Delayed accpetance parameters.
        coarsening = 16                         # nx used in cheap likelihood approximation.
        num_steps_coarse = 60                   # Number of timesteps evaluated in likelihood approximation.

        # Data augmentation.
        # alpha_star = 0                        # True value for alpha.                          
        var_noise = 0.2                         # Variance of noise added to data (sigma_l should approxiamte this).

        # Open high resolution data file.
        with open(f'Master/Data_eps100_num150000_tau10_alpha0/master_data_{nx}_project', 'rb') as file:
            y_star = pickle.load(file)
        
        # Open low resolution data file.
        with open(f'Master/Data_eps100_num150000_tau10_alpha0/master_data_{coarsening}_project', 'rb') as file:
            y_coarse_star = pickle.load(file)
        
        # Thin high resolution data to correspond with variable time-stepping.
        y_star_thinned = time_organiser(y_star,
                                        dt_min,
                                        dt_max,
                                        tau,
                                        reg,
                                        num_steps
                                        )[:-1] # Make removing last element more elegant!
        
        # Thin low resolution data to correspond with variable time-stepping.
        y_coarse_star_thinned = time_organiser(y_coarse_star,
                                               dt_min,
                                               dt_max,
                                               tau,
                                               reg,
                                               num_steps_coarse
                                               )[:-1] # Make removing last element more elegant!

        # Take mean in space.
        y_star_thinned_av = np.mean(y_star_thinned, axis=1)
        y_coarse_star_thinned_av = np.mean(y_coarse_star_thinned, axis=1)

        # mesh = stretch_mesh(nx=nx, ny=ny)

        # y_star_coarse, __ = master_solver(#nx,
        #                                   #ny,
        #                                   mesh,
        #                                   tau,
        #                                   alpha_star,
        #                                   epsilon,
        #                                   num_steps,
        #                                   dt_min,
        #                                   dt_max,
        #                                   reg
        #                                   )

        # Generate vector of normally distributed 'noise' and add to data.
        noise = np.random.normal(0, var_noise, np.shape(y_star_thinned_av))
        y = y_star_thinned_av + noise
        y_coarse = y_coarse_star_thinned_av + noise # T# This could be better!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # Run delayed acceptance algortihm.
        alpha_list, A_list, ratio_list, reject_first_list = delayed_acceptance(alpha0,
                                                                               y,
                                                                               y_coarse,
                                                                               coarsening, 
                                                                               sigma_q, 
                                                                               sigma_p,
                                                                               sigma_l,
                                                                               mu_p,
                                                                               nx,
                                                                               tau,
                                                                               epsilon,
                                                                               iterations,
                                                                               burnin,
                                                                               num_steps,
                                                                               num_steps_coarse,
                                                                               dt_min,
                                                                               dt_max,
                                                                               reg
                                                                               )

        return(alpha_list,
               A_list,
               ratio_list,
               reject_first_list
               # likelihood_list,
               # likelihood_coarse_list
               )
    
    print(main())
