# PhD-project2
Here are the codes for project 2: Bayesian Inference of the Double Glazing Model.

All the final scripts used for generating results are found in the Final-Results branch. 

- master_script_interpolation and master_script_averages are the scripts used to generate the chains for each method, although each script can
be used individually.
- scripts will need to be altered depending on location and type of data used.

The generated data used in the algorithms can be found at: 
https://uoe-my.sharepoint.com/:f:/g/personal/s1634937_ed_ac_uk/EksHpVR9JpBJlz_atlFKk2cBq7a1b6omgJAiUu3fXrRtdg?e=j7fg4O

- noisy_thinned data is such that noise has already been added, and has been thinne din time to match the chosen variable time-stepping
scheme. Cannot be used for parameters other than the ones given at the bottom of this file.
- master data is the raw data generated by running the solver for very small reoslutions (and then interpolated onto a coarser mesh in space) without
noise. Must formatted accordingly in time to be used by the scripts.
- The number in the file (either 16 or 32) is the resolution of the coarse spatial grid the data is interpolated onto. 32 is used by all the algorithms
and 16 is used for the cheaper likelihood evaluation in the delayed acceptance algorithm.
- averages / interpolation suffix depends on which variation of the likelihood function is being used; data should match suffix of script title.
- Recommend using noisy_thinned data and then comment out any data formatting.

All the pramaters used to generate the data should already be calibrated appropriately for the given data. Otherwise, the parameters used
are as follows:

# Solver parameters.
    alpha0 = 1                              # Initial guess for alpha.
    tau = 1/10                              # Rate of growth of hot wall.
    epsilon = 1/100                         # Diffusion coefficient.
    num_steps = 60                          # Number of steps to run solver for.
    nx = 32                                 # Number of horizontal grid points on mesh (ny = nx).
    ny = 32                                 # Number of vertical grid points on mesh. 
    
    # Variable time-stepping variables.                                                                                                          
    dt_min = 1e-3                           # Inital value for dt.
    dt_max = 0.1                            # Limit of dt values as t appraches infty.
    reg = 10                                # Regularisation constant.

    # MCMC parameters.
    iterations = 2000                       # Number of samples to generate (-burnin).
    burnin = 0                              # Number of burn-in iterations.
    
    # RWMH parameters.
    sigma_q = 0.5                           # Vairance of normal proposal distribution.
    sigma_p = 1                             # Variance of normal prior.
    mu_p = 0                                # Mean of normal prior.
    sigma_l = 0.2                           # Variance in likelihood (estimate of noise in data):

    # Delayed accpetance parameters.
    coarsening = 16                         # nx used in cheap likelihood approximation.
    num_steps_coarse = 60                   # Number of timesteps evaluated in likelihood approximation.

    # Irreversible RWMH varibles.
    alpha = sigma_q * 2/np.pi               # alpha parameter used in gamma proposal, derived from sigma_q.
    beta = np.sqrt(2/np.pi)                 # beta parameter used in gamma proposal.

    # Changing form of irreversilbe variables for use in in-built functions.
    k = alpha                               # 'Shape' parameter for gamma distribution (=alpha).
    theta = 1/beta                          # 'Scale' paramter for gamma distribution (=1/beta).

    # WLB variables.
    n = 100                                 # Number of i.d.d. data sets.
    tol = 1e-5                              # Tolerance of optimiser.
    bracket = (-5,5)                        # Bracket used in Brent scalar optimisation.

    # Data augmentation.
    alpha_star = 0                          # True value for alpha.                          
    var_noise = 0.2                         # Variance of noise added to data (sigma_l should approxiamte this).
