if exist('noCLF') 
   hold off
else
   clf
end;
A = [
7.000000e-001
7.500000e-001
7.500000e-001
7.100000e-001
8.000000e-001
2.800000e-001
];
bar(A, 0.8);
set(gca,'linewidth',2)
set(gca,'fontweight','bold')
set(gca,'fontsize',12)
grid on
box on
title('Delta Test Rankings','FontWeight','bold','FontSize',12)
xlabel('Input parameters','FontWeight','bold','FontSize',12)
ylabel('Delta Metric (normalized)','FontWeight','bold','FontSize',12)
