r = mrjd_sim(1,1000,5,[.5,.1,.2,4,1,.01]);
[alpha,beta,sigma,mu,gamma,lambda] = mrjd_mle(r)

% vim: set ft=matlab:
