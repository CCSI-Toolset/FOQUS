if exist('noCLF') 
   hold off
else
   clf
end;
n = 6;
Y = [
 9.7890000000000001e+001
 9.7430000000000007e+001
 9.4780000000000001e+001
 9.8230000000000004e+001
 1.0000000000000000e+002
 2.0500000000000000e+001
];
ymax = max(Y);
ymin = min(Y);
if (ymax == ymin)
   ymax = ymax * 1.01;
   ymin = ymin * 0.99;
end;
if (ymax == ymin)
   ymax = ymax + 0.01;
   ymin = ymin - 0.01;
end;
bar(Y,0.8);
set(gca,'linewidth',2)
set(gca,'fontweight','bold')
set(gca,'fontsize',12)
grid on
box on
title('MARS Rankings','FontWeight','bold','FontSize',12)
xlabel('Input parameters','FontWeight','bold','FontSize',12)
ylabel('MARS ranks','FontWeight','bold','FontSize',12)
