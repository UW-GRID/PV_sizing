%% Standalone PV-battery system for off-grid applications
% Ghana
% *************************************
clc; close all;
K=24;
days=365;

% PV
PVsize=1700; % Watts
pvData=xlsread('GhanaPV1700W.csv'); % From PVwatts calculator 
pvData=pvData(:,10); %DC Array Output (W)
pvData(1:15,:)=[];
pvData(end,:)=[];
pvDays=reshape(pvData,24,365)';
pvDaysFinal = (interp1(linspace(1,24,24),pvDays',linspace(1,24,24)))*(PVsize/100);
clear vars pvData pvDays


% Electrical demand profiles
demand=xlsread('LibraryMaxLoad.csv');
demand=demand(10,9:55);
demand=demand';
demand= demand(all(~isnan(demand),2),:);
% for i = 1:1:days
%     Load(:,i)=demand;
% end
% demand1=Load;

%% ************************************************************************
SbMax=77000; % Maximum battery state-of-charge (SoC)
SbMin=SbMax*0.5; % Minimum battery state-of-charge (SoC)
InvEff=0.9;
BeffD=0.9;
Xb=zeros(days,K);
Sb=zeros(days,K+1);
%Sb(1,1)=SbMin;
Sb(1,1)=(SbMax-SbMin)/2+SbMin;% Initial battery SoC
Plos=zeros(days,K); % Store excess energy (can be used to power less critical devices or send back to grid)
Preq=zeros(days,K); % Store deficit of energy



for d=1:1:days % Loop over all the days
   for k=1:1:K % Time-steps
       if(pvDaysFinal(k,d)-((1/InvEff)*demand(k,1)))>0 % charging +
          Xb(d,k)=pvDaysFinal(k,d)-((1/InvEff)*demand(k,1)); % surplus energy goes to the battery
       elseif (pvDaysFinal(k,d)-((1/InvEff)*demand(k,1)))<0 % discharging - this value is negative
          Xb(d,k)=(pvDaysFinal(k,d)-((1/InvEff)*demand(k,1)))*(1/BeffD); % Energy out of the battery
       elseif (pvDaysFinal(k,d)-((1/InvEff)*demand(k,1)))==0 
          Xb(d,k)=0; % PV is just enough to supply the load and the losses
       end
       Sb(d,k+1)=Sb(d,k)+ Xb(d,k); 
       if Sb(d,k+1)>=SbMax % maximum limit is reached
          Plos(d,k)=Sb(d,k+1)-SbMax;
          Sb(d,k+1)=SbMax; 
       elseif Sb(d,k+1)<=SbMin % minimum limit is reached
           Preq(d,k)=SbMin-Sb(d,k+1);
           Sb(d,k+1)=SbMin; 
       end
   end
   if d~=days
   Sb(d+1,1)=Sb(d,K+1);
   end
   % d
     
end



%% Plot the results
set(0,'defaultAxesFontName', 'Helvetica')
set(0,'defaultTextFontName', 'Helvetica')
set(0,'defaultlinelinewidth',2)
set(0,'defaultAxesFontSize',16)
set(0,'defaultTextFontSize', 16)
set(0,'DefaultAxesLooseInset',[0,0,0,0])

D=240;
figure1 = figure('Color',[1 1 1]);
h=subplot(2,2,3);

plot(1:K,Sb(D,1:K),'k')
plot(1:K,Sb(5,1:K),'k')
hold on;

set(gca,'XLim',[1 24],'YLim',[0 2000],'XTick',[2 4 6 8 10 12 14 16 18 20 22 24],'XTickLabel',{'2','4','6','8','10','12','14','16','18','20','22','24'});
ylabel('Battery SoC (Wh)');
xlabel('Time (hour)');
h=subplot(2,2,2);

plot(1:K,demand)

set(gca,'XLim',[1 24],'YLim',[0 10000],'XTick',[2 4 6 8 10 12 14 16 18 20 22 24],'XTickLabel',{'2','4','6','8','10','12','14','16','18','20','22','24'});
ylabel('Electrical demand (Wh)');
xlabel('Time (hour)');
h=subplot(2,2,1);

plot(1:K,pvDaysFinal(:,D))
plot(1:K,pvDaysFinal(:,5))

set(gca,'XLim',[1 24],'YLim',[0 20000],'XTick',[2 4 6 8 10 12 14 16 18 20 22 24],'XTickLabel',{'2','4','6','8','10','12','14','16','18','20','22','24'});
ylabel('PV output (Wh)');
xlabel('Time (hour)');
h=subplot(2,2,4);

plot(1:K,Plos(D,:),'-k')
hold on;
plot(1:K,Preq(D,:),'b')
B_legend=legend('Energy not used or stored','Energy deficit');
% set(B_legend,'Location','NorthEast','Orientation','vertical')
set(gca,'XLim',[1 24],'YLim',[0 15000],'XTick',[2 4 6 8 10 12 14 16 18 20 22 24],'XTickLabel',{'2','4','6','8','10','12','14','16','18','20','22','24'});
ylabel('Electrical energy (Wh)');
xlabel('Time (hour)');