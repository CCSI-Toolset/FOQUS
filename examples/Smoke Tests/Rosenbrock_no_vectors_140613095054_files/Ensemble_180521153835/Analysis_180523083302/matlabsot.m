if exist('noCLF') 
   hold off
else
   clf
end;
A = [
4.518977e-001
8.197220e-001
6.917091e-001
5.461490e-001
1.000000e+000
5.937829e-002
];
bar(A, 0.8);
set(gca,'linewidth',2)
set(gca,'fontweight','bold')
set(gca,'fontsize',12)
grid on
box on
title('Sum-of-trees Rankings','FontWeight','bold','FontSize',12)
xlabel('Input parameters','FontWeight','bold','FontSize',12)
ylabel('Sum-of-trees Metric (normalized)','FontWeight','bold','FontSize',12)
