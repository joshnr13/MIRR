pkg load statistics

S = csvread('contract_prices.csv', 1, 1);

mu = mean(S)
sigma = std(S)
variance = var(S)
skew = skewness(S)
kurt = kurtosis(S)

% vim: set ft=matlab:
