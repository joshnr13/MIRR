pkg load statistics

function [mu, sigma, lambda] = estimate(S, deltat)
% Calibrate an OU process by least squares.

if (size(S,2) > size(S,1))
    S = S';
end

[k, dummy, resid] = regress(S(2:end), [ones(size(S(1:end-1))) S(1:end-1)]);
a = k(1);
b = k(2);
lambda = -log(b)/deltat;
mu     = a/(1-b);
sigma  =  std(resid) * sqrt( 2*lambda/(1-b^2) );

end

S = log(csvread('contract_prices_last_year.csv', 1, 1));
[mu, sigma, lambda] = estimate(S, 1)

plot(S)
pause

% OUTPUT:
% mu =  3.4397
% sigma =  0.0055596
% lambda =  0.0083759

% vim: set ft=matlab:
