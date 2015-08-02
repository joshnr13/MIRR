%  S = csvread('benchmark_market_price_timeseries.csv');
S = csvread('price_weekly.csv');

deltas = S(2:end) - S(1:end-1);

disp('Razlike: ')
mu = mean(deltas)
sigma = std(deltas)

disp('------------------')

disp('Log-razlike: ')
ld = abs(deltas);
ld(ld == 0) = []; % filter out zeros
ld = log(ld);

mu = mean(ld)
sigma = std(ld)

hist(deltas, 100)
pause
hist(ld, 100)
pause

% vim: set ft=matlab:
