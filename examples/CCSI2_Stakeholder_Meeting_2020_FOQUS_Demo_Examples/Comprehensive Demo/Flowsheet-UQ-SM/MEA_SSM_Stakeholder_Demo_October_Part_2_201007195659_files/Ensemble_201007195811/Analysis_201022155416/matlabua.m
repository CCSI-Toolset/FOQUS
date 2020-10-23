Y = [
   9.0793651400000002e+001
   8.0099091999999999e+001
   9.9961822900000001e+001
   9.9949893399999993e+001
   9.2884263899999993e+001
   7.4498173899999998e+001
   9.9976674299999999e+001
   9.9915602699999994e+001
   8.6953569999999999e+001
   9.7600758299999995e+001
   9.9592882799999998e+001
   9.9863298499999999e+001
   9.9803392900000006e+001
   8.3747081800000004e+001
   9.6695968300000004e+001
   9.9935498400000000e+001
   7.1415536000000003e+001
   9.9036550800000001e+001
   7.7641027300000005e+001
   9.9977408600000004e+001
];
if exist('noCLF') 
   hold off
else
   clf
end;
twoPlots = 0;
if (twoPlots == 1)
subplot(1,2,1)
end;
[nk,xk]=hist(Y(:,1),10);
bar(xk,nk/20,1.0)
set(gca,'linewidth',2)
set(gca,'fontweight','bold')
set(gca,'fontsize',12)
grid on
box on
title('Probability Distribution','FontWeight','bold','FontSize',12)
xlabel('MEA_UPD.CO2CAPTURE','FontWeight','bold','FontSize',12)
ylabel('Probabilities','FontWeight','bold','FontSize',12)
if (twoPlots == 1)
Yk = sort(Y(:,1));
Xk = 1 : 20;
Xk = Xk / 20;
subplot(1,2,2)
plot(Yk, Xk, 'lineWidth',3)
set(gca,'linewidth',2)
set(gca,'fontweight','bold')
set(gca,'fontsize',12)
grid on
box on
title('Cumulative Distribution','FontWeight','bold','FontSize',12)
xlabel('MEA_UPD.CO2CAPTURE','FontWeight','bold','FontSize',12)
ylabel('Probabilities','FontWeight','bold','FontSize',12)
end;
