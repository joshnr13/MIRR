pkg load statistics

function [mu, sigma, lambda] = estimateLS(S, deltat)
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
function [ mu, sigma, lambda ] = estimateML(S, deltat)
  % Calibrate an OU process by maximum likelihood.
  n = length(S)-1;
  Sx  = sum( S(1:end-1) );
  Sy  = sum( S(2:end) );
  Sxx = sum( S(1:end-1).^2 );
  Sxy = sum( S(1:end -  1  ).*S(2:end) );
  Syy = sum( S(2:end).^2 );
  mu  = (Sy*Sxx  -  Sx*Sxy) / ( n*(Sxx  -  Sxy)  -  (Sx^2  -  Sx*Sy) );
  lambda =  -  (1/deltat)*log((Sxy  -  mu*Sx  -  mu*Sy + n*mu^2) / (Sxx  -  2*mu*Sx + n*mu^2));  alpha  = exp(  -  lambda*deltat);
  alpha2 = exp(  -  2*lambda  *deltat);  sigmahat2 = (1/n)*(Syy  -  2*alpha*Sxy + alpha2*Sxx  -  ...
    2*mu*(1  -  alpha)*(Sy  -  alpha*Sx) + n*mu^2*(1  -  alpha)^2);
  sigma = sqrt(sigmahat2*2*lambda/(1  -  alpha2));
end

S = log(csvread('contract_prices.csv', 1, 1));
format long
disp('LS:')
[mu, sigma, lambda] = estimateLS(S, 1)
disp('MLE:')
[mu, sigma, lambda] = estimateML(S, 1)

pause

% OUTPUT:
% mu =  3.4397
% sigma =  0.0055596
% lambda =  0.0083759

% vim: set ft=matlab:
