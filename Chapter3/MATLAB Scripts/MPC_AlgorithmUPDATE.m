%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Kaden Plewe
% U0896242
% MPC in a small office building thermal model
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

clear, clc, close all

%% Define state space model
A = xlsread('Building_State-Space.xlsx', 'A (3)');
D = [-30.66; -20.44; -30.66; -20.44; 0; -209.57];
% A(end) = A(end)*100;

% A(5, 5) = 500;
% A(6, 6) = 800;

% Unit conversion variables
stepT = 15;         % minute timestep
dt = 60*stepT;     % timestep in seconds
Cap = [419571.7 248587.1 419038.9 248575. 552784.5 872168.1]; %(J/C) thermal capacitance for each thermal zone
% 0.5: 309513.8
% Cap = -1*[41957.17 24858.71 41903.89 24857.5 55278.45 87216.81]; %(J/C) thermal capacitance for each thermal zone
% Cap = -1*[4195.717 2485.871 4190.389 2485.75 5527.845 8721.681]; %(J/C) thermal capacitance for each thermal zone
A = bsxfun(@times, 1./Cap', A);
B = 1./Cap';
D = D.*1./Cap';

% A_hat = expm(dt*A);
% B_hat = diag(1 - exp(-dt*B));
% B_hat(end) = 0;
% D_hat = (1 - exp(-dt*D));

A_hat = eye(6) - dt*A;
D_hat = -dt*D;
B_hat = dt*diag(B);
B_hat(end) = 0;
%% Load data
Temp = xlsread('outdoortemp.xlsx'); % dry bulb temp for full yr in LA, MI
winter2day = Temp(1:2880, :); % january 1st and 2nd
% winter2day = Temp(1:10000, :); % january 1st and 2nd
Jan17week = Temp(24480:34560, :); % january 17st and 18nd
timeSeries = [decimate(Jan17week(:, 1), stepT), decimate(Jan17week(:, 2), stepT)];
timeSeries(:, 1) = 1:1:length(timeSeries(:, 2));

%% Compute and plot isolated behavior (no heat input)

colors = ['r', 'g', 'b', 'm', 'k']; %zones 1-5
Tiso = zeros(6, length(timeSeries(:, 1)));
% Tiso(:, 1) = ones(6, 1)*0;
Tiso(:, 1) = ones(6, 1)*timeSeries(1, 2);
for i = 2:length(timeSeries(:, 1))
    %compute indoor temperatures
    Tiso(:, i) = A_hat*Tiso(:, i-1) + D_hat*timeSeries(i-1, 2); 
end

figure(2)
hold on
plot(timeSeries(:, 1), Tiso(1, :), colors(1))
plot(timeSeries(:, 1), Tiso(2, :), colors(2))
plot(timeSeries(:, 1), Tiso(3, :), colors(3))
plot(timeSeries(:, 1), Tiso(4, :), colors(4))
plot(timeSeries(:, 1), Tiso(5, :), colors(5))
plot(timeSeries(:, 1), timeSeries(:, 2), '-.k')
xlabel('Time (h)')
ylabel('Temperature (°C)')
legend('Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Outdoor')

%% Run a simple on/off simulation
t_end = 60;

% initializing state variables
sp = ones(6, 1)*22;            % setpoint temperature (C)
sp(end) = 0;
To = Temp(:, 2);            % ambient temperature (C)
T = zeros(6, t_end);        % zone temperatures   (C)
T0 = 22;                    % initial condition   (C)
T(:, 1) = ones(6, 1)*T0;    
qin = zeros(6, t_end);          % zone heat input
q = [4000; 3000; 4000; 3000; 2500; 0];    % constant heat input for on/off
onFlag = 0;

for k = 2:t_end-1   
    disp(T(1:5, k-1) - sp(1:5) < 1)
%     if onFlag == 1
%         if any(T(1:5, k-1) - sp(1:5) < 1)
%             qin(1:5, k) = q(1:5).*(T(1:5, k-1) - sp(1:5) < 1);
%             onFlag = 1;
%         else
%             qin(:, k) = 0;
%             onFlag = 0;
%         end
%     else    
        if any(T(1:5, k-1) - sp(1:5) < 0)
            qin(1:5, k) = q(1:5).*(T(1:5, k-1) - sp(1:5) < 0);
            onFlag = 1;
        else
            onFlag = 0;
            qin(:, k) = 0;
        end
%     end
    T(:, k) = A_hat*T(:, k-1) + B_hat*qin(:, k-1) + D_hat*To(k-1);
    T(:, k)'
    k
end

%% Plot state and control trajectory for on/off method

close all
figure(1)
plot(1:size(T, 2), T)
hold on
plot(1:size(T, 2), To(1:size(T, 2)), 'k--')
xlabel('Time (min)')
ylabel('Temperature (°C)')
legend('Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Attic', 'Outdoor')
ylim([-20, 30])

figure(2)
plot(1:size(qin, 2), qin)
xlabel('Time (h)')
ylabel('Heat Input (W)')
legend('Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Attic', 'Outdoor')


%% Generate setpoint schedule that matches those used in energy plus
clgmultiplier = ones(6, 1);
clgmultiplier(end) = 1000;
clgSP1 = clgmultiplier*29.44;     % for 0:00 - 6:00
clgSP2 = clgmultiplier*27.8;      % for 6:00 - 7:00
clgSP3 = clgmultiplier*25.6;      % for 7:00 - 8:00
clgSP4 = clgmultiplier*23.89;     % for 8:00 - 18:00
clgSP5 = clgmultiplier*29.44;     % for 18:00 - 24:00

htgmultiplier = ones(6, 1);
htgmultiplier(end) = -1000;
htgSP1 = htgmultiplier*15.56;     % for 0:00 - 6:00
htgSP2 = htgmultiplier*17.8;      % for 6:00 - 7:00
htgSP3 = htgmultiplier*20;      % for 7:00 - 8:00
htgSP4 = htgmultiplier*21.11;     % for 8:00 - 19:00
htgSP5 = htgmultiplier*15.56;     % for 19:00 - 24:00

% generate cooling and heating setpoint vector that is the same size as the
% expected optimal control input and impliments the schedule listed above
T_clg_cell = cell(60/stepT*24, 1);
T_htg_cell = cell(60/stepT*24, 1);

% generate set of cooling setpoints for one day
for i = 1:length(T_clg_cell)
   if i*stepT/60 <= 6
       T_clg_cell(i) = {clgSP1};
   elseif i*stepT/60 > 6 && i*stepT/60 <= 7
       T_clg_cell(i) = {clgSP2};    
   elseif i*stepT/60 >7 && i*stepT/60 <= 8
       T_clg_cell(i) = {clgSP3};    
   elseif i*stepT/60 > 8 && i*stepT/60 <= 18
       T_clg_cell(i) = {clgSP4};    
   else
       T_clg_cell(i) = {clgSP5};
   end
end
T_clg = cell2mat(T_clg_cell);

% generate set of heating setpoints for one day
for i = 1:length(T_htg_cell)
   if i*stepT/60 <= 6
       T_htg_cell(i) = {htgSP1};
   elseif i*stepT/60 > 6 && i*stepT/60 <= 7
       T_htg_cell(i) = {htgSP2};    
   elseif i*stepT/60 >7 && i*stepT/60 <= 8
       T_htg_cell(i) = {htgSP3};    
   elseif i*stepT/60 > 8 && i*stepT/60 <= 19
       T_htg_cell(i) = {htgSP4};    
   else
       T_htg_cell(i) = {htgSP5};
   end
end
T_htg = cell2mat(T_htg_cell);

figure()
hold on
plot(T_htg, 'ob')
plot(T_clg, 'or')
ylim([15, 30])

%% Run MPC algorithm over a two day horizon with on/off control

% horizon and simulation time
t_end = 24*60/stepT;
N = 24*60/stepT;

% weighting function for cost
rho = 0.1;
Q = eye(N*6)*rho;

psi = 5000;
R = eye(N*6)*psi;
R(end) = 0;

% initializing state variables
sp = ones(6, 1)*23;            % setpoint temperature (C)
sp(end) = 0;
To = Jan17week(:, 2);            % ambient temperature (C)
T = zeros(6, t_end);        % zone temperatures   (C)
T0 = 15.56;                    % initial condition   (C)
T(:, 1) = ones(6, 1)*T0;    
qin = zeros(6, N);          % zone heat input
q = [4000; 3000; 4000; 3000; 2500; 0];    % constant heat input for on/off

P = zeros(6);               % matrix used to index out the attic zone
P(end) = 1;
I = eye(6);                 % identity matrix being added to A

% create augmented A matrix, M
M_cell=cell(N, 1);
for i=1:N
    M_cell(i)={A_hat^i};
end
M=cell2mat(M_cell);

% create augmented C matrix C_dec
C_dec_cell=cell(N);
for i=1:N
    for j=1:N
        if i>=j
            C_dec_cell(i,j)={B_hat};
        else
            C_dec_cell(i,j)={zeros(size(B_hat))};
        end
    end
end

for i=1:N
    for j=1:N
        if i>j
            C_dec_cell(i,j)={A_hat^(i-j)*C_dec_cell{i,j}};
        end
    end
end
C_dec=cell2mat(C_dec_cell);

% create augmented D matrix for ambient temperature consideration
D_dec_cell=cell(N);
for i=1:N
    for j=1:N
        if i>=j
            D_dec_cell(i,j)={diag(D_hat)};
        else
            D_dec_cell(i,j)={zeros(length(D_hat))};
        end
    end
end

for i=1:N
    for j=1:N
        if i>j
            D_dec_cell(i,j)={A_hat^(i-j)*D_dec_cell{i,j}};
        end
    end
end
D_dec=cell2mat(D_dec_cell);

% ambient temperature disturbance matrix
Tamb = zeros(length(To)*6, 1);
j = 1;
for i = 1:length(To)
   Tamb(j:j+5) = ones(6, 1)*To(i); 
   j = j + 6;
end

% Dp = zeros(6*N, 1);
% for i = 1:6:6*N
%    Dp(i:i+5) = D_hat;
% end
% Dp = diag(Dp);

% matrix for extracting attic heat input
P_cell=cell(N);
for i=1:N
    for j=1:N
        if i==j
            P_cell(i,j)={P};
        else
            P_cell(i,j)={zeros(size(P))};
        end
    end
end
P = cell2mat(P_cell);

% augmented matrix for neglecting attic temperature
B_cell=cell(N);
for i=1:N
    for j=1:N
        if i==j
            B_cell(i,j)={B_hat};
        else
            B_cell(i,j)={zeros(size(B_hat))};
        end
    end
end
Bn = cell2mat(B_cell);

% cooling and heating setpoint constraints
clgSP = ones(6, 1)*24;
clgSP(end) = 1000;
htgSP = ones(6, 1)*20;
htgSP(end) = -1000;
clgSP_cell=cell(N, 1);
htgSP_cell=cell(N, 1);
sp_cell=cell(N, 1);
for i=1:N
    clgSP_cell(i)={clgSP};
    htgSP_cell(i)={htgSP};
    sp_cell(i)={sp};
end
clgSP=cell2mat(clgSP_cell);
htgSP=cell2mat(htgSP_cell);
sp=cell2mat(sp_cell);


% define state variables used in prediction and optimization
x = zeros(6*t_end, 1);
x(1:6) = ones(6, 1)*T0;

% run simulation for defined period with temperature band constraints
% + ...
%         (P*(M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1)) - sp))' ...
%         *R*(P*((M*T(:, k) + C_dec*u + ...
%         D_dec*Tamb(6*k-5:6*k-5+(6*N-1)) - sp))))
for k = 1:t_end-1
    % generate set of cooling setpoints for this prediction horizon
    clgSP = T_clg(6*k+1:end);
    htgSP = T_htg(6*k+1:end);
    for i = 1:N/(stepT*24)-1
       clgSP = [clgSP; T_clg];
       htgSP = [htgSP; T_htg]; 
    end
    clgSP = [clgSP; T_clg(1:6*k)];
    htgSP = [htgSP; T_htg(1:6*k)];
        
%     figure()
%     hold on
%     plot(clgSP, 'or')
%     plot(htgSP, 'ob')
%     ylim([15, 30])
      
    cvx_begin quiet
    variable u(6*N)
    minimize (u'*Q*u + ...
        ((M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1)) - htgSP))' ...
        *R*(((M*T(:, k) + C_dec*u + ...
        D_dec*Tamb(6*k-5:6*k-5+(6*N-1)) - htgSP)))) % Frobenius norm with weight Q and R
    subject to 
    u >= 0
    u <= 5000
    P*u == 0
    disp(size((M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1)))))
    (M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1))) <= clgSP
    (M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1))) >= htgSP

    cvx_end

    qin(:, k) = q.*(u(1:6)>q./2);
    x(6*k-5:6*k-5+(6*N-1)) = (M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1)));
    T(:, k+1) = A_hat*T(:, k) + B_hat*qin(:, k) + D_hat*To(k);
    k
end

%% Plot state and control trajectory

close all
figure(1)
plot(1:size(T, 2), T)
hold on
plot(1:size(T, 2), To(1:size(T, 2)), 'k--')
xlabel('Time (min)')
ylabel('Temperature (°C)')
legend('Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Attic', 'Outdoor')
ylim([-20, 30])

figure(2)
stairs(1:size(qin, 2), qin')
xlabel('Time (h)')
ylabel('Heat Input (W)')
legend('Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Attic', 'Outdoor')


%% Run MPC algorithm over a two day horizon with variable control

% horizon and simulation time
t_end = 24*60/stepT;
N = 24*60/stepT;

% weighting function for cost
rho = 0.001;
Q = eye(N*6)*rho;

psi = 5000;
R = eye(N*6)*psi;
R(end) = 0;

phi = 0;
Q_tilde = eye(N*6)*phi;

Diff = ones(6, 1);
Diff(end) = 0;
Diff_cell = cell(N, 1);
for i=1:N-1
    Diff_cell(i)={Diff};
end
Diff = cell2mat(Diff_cell);
Diff = diag(Diff(1:end), 6);

% initializing state variables
sp = ones(6, 1)*23;            % setpoint temperature (C)
sp(end) = 0;
To = Jan17week(:, 2);            % ambient temperature (C)
T = zeros(6, t_end);        % zone temperatures   (C)
T0 = 15.56;                    % initial condition   (C)
T(:, 1) = ones(6, 1)*T0;    
qin = zeros(6, N);          % zone heat input
q = [4000; 3000; 4000; 3000; 2500; 0];    % constant heat input for on/off

P = zeros(6);               % matrix used to index out the attic zone
P(end) = 1;
I = eye(6);                 % identity matrix being added to A

% create augmented A matrix, M
M_cell=cell(N, 1);
for i=1:N
    M_cell(i)={A_hat^i};
end
M=cell2mat(M_cell);

% create augmented C matrix C_dec
C_dec_cell=cell(N);
for i=1:N
    for j=1:N
        if i>=j
            C_dec_cell(i,j)={B_hat};
        else
            C_dec_cell(i,j)={zeros(size(B_hat))};
        end
    end
end

for i=1:N
    for j=1:N
        if i>j
            C_dec_cell(i,j)={A_hat^(i-j)*C_dec_cell{i,j}};
        end
    end
end
C_dec=cell2mat(C_dec_cell);

% create augmented D matrix for ambient temperature consideration
D_dec_cell=cell(N);
for i=1:N
    for j=1:N
        if i>=j
            D_dec_cell(i,j)={diag(D_hat)};
        else
            D_dec_cell(i,j)={zeros(length(D_hat))};
        end
    end
end

for i=1:N
    for j=1:N
        if i>j
            D_dec_cell(i,j)={A_hat^(i-j)*D_dec_cell{i,j}};
        end
    end
end
D_dec=cell2mat(D_dec_cell);

% ambient temperature disturbance matrix
Tamb = zeros(length(To)*6, 1);
j = 1;
for i = 1:length(To)
   Tamb(j:j+5) = ones(6, 1)*To(i); 
   j = j + 6;
end

% Dp = zeros(6*N, 1);
% for i = 1:6:6*N
%    Dp(i:i+5) = D_hat;
% end
% Dp = diag(Dp);

% matrix for extracting attic heat input
P_cell=cell(N);
for i=1:N
    for j=1:N
        if i==j
            P_cell(i,j)={P};
        else
            P_cell(i,j)={zeros(size(P))};
        end
    end
end
P = cell2mat(P_cell);

% augmented matrix for neglecting attic temperature
B_cell=cell(N);
for i=1:N
    for j=1:N
        if i==j
            B_cell(i,j)={B_hat};
        else
            B_cell(i,j)={zeros(size(B_hat))};
        end
    end
end
Bn = cell2mat(B_cell);

% cooling and heating setpoint constraints
clgSP = ones(6, 1)*24;
clgSP(end) = 1000;
htgSP = ones(6, 1)*20;
htgSP(end) = -1000;
clgSP_cell=cell(N, 1);
htgSP_cell=cell(N, 1);
sp_cell=cell(N, 1);
for i=1:N
    clgSP_cell(i)={clgSP};
    htgSP_cell(i)={htgSP};
    sp_cell(i)={sp};
end
clgSP=cell2mat(clgSP_cell);
htgSP=cell2mat(htgSP_cell);
sp=cell2mat(sp_cell);


% define state variables used in prediction and optimization
x = zeros(6*t_end, 1);
x(1:6) = ones(6, 1)*T0;

% run simulation for defined period with temperature band constraints
% + ...
%         (P*(M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1)) - sp))' ...
%         *R*(P*((M*T(:, k) + C_dec*u + ...
%         D_dec*Tamb(6*k-5:6*k-5+(6*N-1)) - sp))))
for k = 1:t_end-1
    % generate set of cooling setpoints for this prediction horizon
    clgSP = T_clg(6*k+1:end);
    htgSP = T_htg(6*k+1:end);
    for i = 1:0
       clgSP = [clgSP; T_clg];
       htgSP = [htgSP; T_htg]; 
    end
    clgSP = [clgSP; T_clg(1:6*k)];
    htgSP = [htgSP; T_htg(1:6*k)];
        
%     figure()
%     hold on
%     plot(clgSP, 'or')
%     plot(htgSP, 'ob')
%     ylim([15, 30])
%       
    cvx_begin quiet
    variable u(6*N)
    minimize (u'*Q*u +  (u - Diff*u)'*Q_tilde*(u - Diff*u) +...
        ((M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1)) - (htgSP+1)))' ...
        *R*(((M*T(:, k) + C_dec*u + ...
        D_dec*Tamb(6*k-5:6*k-5+(6*N-1)) - (htgSP+1))))) % Frobenius norm with weight Q and R
    subject to 
    u >= 0
    u <= 5000
    P*u == 0
    disp(size((M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1)))))
    (M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1))) <= clgSP
    (M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1))) >= htgSP

    cvx_end

    qin(:, k) = u(1:6);
    x(6*k-5:6*k-5+(6*N-1)) = (M*T(:, k) + C_dec*u + D_dec*Tamb(6*k-5:6*k-5+(6*N-1)));
    T(:, k+1) = A_hat*T(:, k) + B_hat*qin(:, k) + D_hat*To(k);
    T(:, k+1)'
    qin(:, k)'
    k
end

%% Plot state and control trajectory

close all
figure(1)
plot(1:size(T, 2), T)
hold on
plot(1:size(T, 2), To(1:size(T, 2)), 'k--')
xlabel('Time (min)')
ylabel('Temperature (°C)')
legend('Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Attic', 'Outdoor')
ylim([-20, 30])

figure(2)
stairs(1:size(qin, 2), qin')
xlabel('Time (h)')
ylabel('Heat Input (W)')
legend('Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Attic', 'Outdoor')




