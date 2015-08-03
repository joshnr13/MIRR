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

disp('------------------')

disp('Log-cene: ')
lc = log(S);
mu = mean(lc)
sigma = std(lc)

disp('------------------')

disp('Log-cene-razlike: ')
ldeltas = lc(2:end) - lc(1:end-1);

mu = mean(ldeltas)
sigma = std(ldeltas)

hist(deltas, 100)
pause
hist(ld, 100)
pause
hist(lc, 100)
pause
hist(ldeltas, 100)
pause

% vim: set ft=matlab:
