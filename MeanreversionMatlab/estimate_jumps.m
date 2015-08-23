S = log(csvread('contract_prices.csv', 1, 1));
[alpha,beta,sigma,mu,gamma,lambda] = mrjd_mle(S)

% vim: set ft=matlab:
