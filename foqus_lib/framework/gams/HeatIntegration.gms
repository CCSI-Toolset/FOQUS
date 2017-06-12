* LP and MILP Transshipment model for heat integration
* by Yang Chen, start on 2012-12-18, modified on 2013-1-23

* Setup output format
* listing of the input file on or off
* $offlisting
* cross reference map on or off
* $offsymxref
* symbol list on or off
* $offsymlist
* number of equations listed per block in list file
* Option limrow = 100;
* number of variables listed per block in list file
* Option limcol = 100;
* solver status on or off
* Option sysout = off;
* solution report on or off
* Option solprint = off;


$include GamsInput.inc


Alias (K, K2, K3);

Alias (H, H2, H3);
Alias (C, C2, C3);
Alias (S, S2, S3);
Alias (W, W2, W3);

Parameters
    TH(K)  hot side end points of temperature intervals
    TC(K)  cold side end points of temperature intervals
    NKT  actual number of end points of temperature intervals
    NK  actual number of temperature intervals ;

TH(K) = 0;
TC(K) = 0;

Parameter Tmax  the maximum temperature of process streams ;
Parameter Tmin  the minimum temperature of process streams ;

Scalar temp  a temporary parameter  / 0 / ;
Scalar temp2  a temporary parameter  / 0 / ;
Scalar temp3  a temporary parameter  / 0 / ;
Scalar temp4  a temporary parameter  / 0 / ;
scalar ind  a indicator  / 1 /;
scalar ind2  a indicator  / 1 /;

Tmax = max( smax(H, TinH(H)), smax(C, ToutC(C) + dT) );
Tmin = min( smin(H, ToutH(H)), smin(C, TinC(C) + dT) );

TH(K)$(ord(K) = 1) = Tmax;

temp2 = Tmax;

Loop(K $ (ord(K) > 1 and ind = 1),
     temp = 0;
     ind = 0;
     Loop(H $ (TinH(H) < Tmax and TinH(H) > Tmin and TinH(H) > temp and TinH(H) < temp2),
          temp = TinH(H);
          ind = 1;
         );
     Loop(C $ (TinC(C)+dT < Tmax and TinC(C)+dT > Tmin and TinC(C)+dT > temp and TinC(C)+dT < temp2),
          temp = TinC(C) + dT;
          ind = 1;
         );
     Loop(S $ (TinS(S) < Tmax and TinS(S) > Tmin and TinS(S) > temp and TinS(S) < temp2),
          temp = TinS(S);
          ind = 1;
         );
     Loop(W $ (TinW(W)+dT < Tmax and TinW(W)+dT > Tmin and TinW(W)+dT > temp and TinW(W)+dT < temp2),
          temp = TinW(W) + dT;
          ind = 1;
         );
     Loop(H $ (ToutH(H) < Tmax and ToutH(H) > Tmin and ToutH(H) > temp and ToutH(H) < temp2),
          temp = ToutH(H);
          ind = 1;
         );
     Loop(C $ (ToutC(C)+dT < Tmax and ToutC(C)+dT > Tmin and ToutC(C)+dT > temp and ToutC(C)+dT < temp2),
          temp = ToutC(C) + dT;
          ind = 1;
         );
     TH(K) = temp;
     temp2 = temp;
     NKT = ord(K);
    );

TH(K)$(ord(K) = NKT) = Tmin;

TC(K) = TH(K) - dT $ (ord(K) <= NKT);

NK = NKT - 1;

display TH, TC;
Parameters
    THA0(K)  hot side end points of temperature intervals for area targeting
    TCA0(K)  cold side end points of temperature intervals for area targeting
    NKAT0  actual number of end points of temperature intervals for area targeting
    NKA0  actual number of temperature intervals for area targeting  ;

THA0(K) = 0;
TCA0(K) = 0;

Parameters
    deltaT(K)  size of temperature interval
    deltaTmin  minimum size of temperature interval
    deltaTmean  mean size of temperature interval ;

deltaT(K) = 0;
deltaTmin = 0;
deltaTmean = 0;

Parameters
    Nad(K)  number of divisions for area temperature intervals;

Nad(K) = 0;

Parameters
    THA(K)  hot side end points of temperature intervals for area targeting
    TCA(K)  cold side end points of temperature intervals for area targeting
    NKA  actual number of temperature intervals for area targeting  ;

THA(K) = 0;
TCA(K) = 0;

Parameters
    deltaThot(K,K2)  hot side temperature difference between intervals
    deltaTcold(K,K2)  cold side temperature difference between intervals
    LMTD(K,K2)  logarithmic-mean temperature difference betweeen intervals ;

deltaThot(K,K2) = 0;
deltaTcold(K,K2) = 0;
LMTD(K,K2) = 0;

Tmax = max( smax(H, TinH(H)), smax(C, ToutC(C)+dTA), smax(S, TinS(S)) );
Tmin = min( smin(H, ToutH(H)), smin(C, TinC(C)+dTA), smin(W, TinW(W)+dTA) );

THA0(K)$(ord(K) = 1) = Tmax;

temp2 = Tmax;

ind = 1;

Loop(K $ (ord(K) > 1 and ind = 1),
     temp = 0;
     ind = 0;
     Loop(H $ (TinH(H) < Tmax and TinH(H) > Tmin and TinH(H) > temp and TinH(H) < temp2),
          temp = TinH(H);
          ind = 1;
         );
     Loop(C $ (TinC(C)+dTA < Tmax and TinC(C)+dTA > Tmin and TinC(C)+dTA > temp and TinC(C)+dTA < temp2),
          temp = TinC(C) + dTA;
          ind = 1;
         );
     Loop(S $ (TinS(S) < Tmax and TinS(S) > Tmin and TinS(S) > temp and TinS(S) < temp2),
          temp = TinS(S);
          ind = 1;
         );
     Loop(W $ (TinW(W)+dTA < Tmax and TinW(W)+dTA > Tmin and TinW(W)+dTA > temp and TinW(W)+dTA < temp2),
          temp = TinW(W) + dTA;
          ind = 1;
         );
     Loop(H $ (ToutH(H) < Tmax and ToutH(H) > Tmin and ToutH(H) > temp and ToutH(H) < temp2),
          temp = ToutH(H);
          ind = 1;
         );
     Loop(C $ (ToutC(C)+dTA < Tmax and ToutC(C)+dTA > Tmin and ToutC(C)+dTA > temp and ToutC(C)+dTA < temp2),
          temp = ToutC(C) + dTA;
          ind = 1;
         );
     THA0(K) = temp;
     temp2 = temp;
     NKAT0 = ord(K);
    );

THA0(K)$(ord(K) = NKAT0) = Tmin;

TCA0(K) = THA0(K) - dTA $ (ord(K) <= NKAT0);

NKA0 = NKAT0 - 1;

Loop(K $ (ord(K) <= NKA0),
     deltaT(K) = THA0(K) - THA0(K+1);
    );

deltaTmin = smin(K$(ord(K)<=NKA0), deltaT(K));

deltaTmean = max(3*deltaTmin, dTA);

Loop(K $ (ord(K) <= NKAT0),
     Nad(K) = ceil(deltaT(K)/deltaTmean);
    );

Scalars
    index1   / 0 /
    index2   / 0 /;

THA(K)= THA0(K) $ (ord(K) = 1);

Loop(K $ (ord(K) >= 2 and ord(K) <= NKAT0),
     If(ord(K) = 2,
        index1 = 1;
     Else
        index1 = index1 + Nad(K-2);
       );
     index2 = index1 + Nad(K-1);

     Loop(K2 $ (ord(K2) > index1 and ord(K2) <= index2),
          THA(K2) = THA0(K-1) + (ord(K2) - index1)*(THA0(K) - THA0(K-1))/Nad(K-1);
         );
    );

NKA = sum(K$(ord(K)<=NKA0), Nad(K));

TCA(K) = THA(K) - dTA $ (ord(K) <= NKA+1);


Loop(K $ (ord(K) <= NKA),
     Loop(K2 $ (ord(K2) >= ord(K) and ord(K2) <= NKA),
          deltaThot(K,K2) = THA(K) - TCA(K2);
          deltaTcold(K,K2) = THA(K+1) - TCA(K2+1);
          If(deltaThot(K,K2) = deltaTcold(K,K2),
             LMTD(K,K2) = (deltaThot(K,K2)*deltaTcold(K,K2)*(deltaThot(K,K2)+deltaTcold(K,K2))/2)**(1/3);
          Else
             LMTD(K,K2) = (deltaThot(K,K2) - deltaTcold(K,K2))/(log(deltaThot(K,K2)/deltaTcold(K,K2)));
            );
         );
    );


* Determine whether some process stream in within some temperature interval
Parameters
    Hk(H,K)  hot process stream within temperature interval
    Hkp(H,K)  hot process stream within and above temperature interval
    Ck(C,K)  cold process stream within temperature interval
    Sk(S,K)  hot utility stream within temperature interval
    Skp(S,K)  hot utility stream within and above temperature interval
    Wk(W,K)  cold utility stream within temperature interval ;

Hk(H,K) = 0;
Hkp(H,K) = 0;
Ck(C,K) = 0;
Sk(S,K) = 0;
Skp(S,K) = 0;
Wk(W,K) = 0;

Loop(K $ (ord(K) <= NK),
     Hk(H,K) = 1 $ (TinH(H) >= TH(K) and ToutH(H) < TH(K));
     Hkp(H,K) = 1 $ (TinH(H) >= TH(K));
     Ck(C,K) = 1 $ (TinC(C) <= TC(K+1) and ToutC(C) > TC(K+1));
     Sk(S,K) = 1 $ ((TinS(S) >= TH(K) and ToutS(S) < TH(K))
                    or (TinS(S) > TH(K) and ord(K) = 1));
     Skp(S,K) = 1 $ (TinS(S) >= TH(K));
     Wk(W,K) = 1 $ ((TinW(W) <= TC(K+1) and ToutW(W) > TC(K+1))
                    or (TinW(W) < TC(K+1) and ord(K) = NK));
    );

Scalar indK  indicator for temperature intervals for utilities  / 1 / ;
Loop(S,
     If(sum(K$(ord(K) <= NK), Sk(S,K)) > 1,
        indK = 1;
        Loop(K $ (Sk(S,K) = 1 and ord(K) <= NK),
             If(indK = 0,
                Sk(S,K) = 0;
               );
             If(Sk(S,K) = 1,
                indK = 0;
               );
            );
       );
    );
Loop(W,
     If(sum(K$(ord(K) <= NK), Wk(W,K)) > 1,
        indK = 1;
        Loop(K $ (ord(K) <= NK),
             Loop(K2 $ (ord(K2) = NK + 1 - ord(K) and Wk(W,K2) = 1),
                  If(indK = 0,
                     Wk(W,K2) = 0;
                    );
                  If(Wk(W,K2) = 1,
                     indK = 0;
                    );
                 );
            );
       );
    );


Parameters
    HAk(H,K)  hot process stream within temperature interval for area targeting
    HAkp(H,K)  hot process stream within and above temperature interval for area targeting
    CAk(C,K)  cold process stream within temperature interval for area targeting
    SAk(S,K)  hot utility stream within temperature interval for area targeting
    SAkp(S,K)  hot utility stream within and above temperature interval for area targeting
    WAk(W,K)  cold utility stream within temperature interval for area targeting  ;

HAk(H,K) = 0;
HAkp(H,K) = 0;
CAk(C,K) = 0;
SAk(S,K) = 0;
SAkp(S,K) = 0;
WAk(W,K) = 0;

Loop(K $ (ord(K) <= NKA),
     HAk(H,K) = 1 $ (TinH(H) >= THA(K) and ToutH(H) < THA(K));
     HAkp(H,K) = 1 $ (TinH(H) >= THA(K));
     CAk(C,K) = 1 $ (TinC(C) <= TCA(K+1) and ToutC(C) > TCA(K+1));
     SAk(S,K) = 1 $ ((TinS(S) >= THA(K) and ToutS(S) < THA(K)));
     SAkp(S,K) = 1 $ (TinS(S) >= THA(K));
     WAk(W,K) = 1 $ ((TinW(W) <= TCA(K+1) and ToutW(W) > TCA(K+1)));
    );

indK = 1;
Loop(S,
     If(sum(K$(ord(K) <= NKA), SAk(S,K)) > 1,
        indK = 1;
        Loop(K $ (SAk(S,K) = 1 and ord(K) <= NKA),
             If(indK = 0,
                SAk(S,K) = 0;
               );
             If(SAk(S,K) = 1,
                indK = 0;
               );
            );
       );
    );
Loop(W,
     If(sum(K$(ord(K) <= NKA), WAk(W,K)) > 1,
        indK = 1;
        Loop(K $ (ord(K) <= NKA),
             Loop(K2 $ (ord(K2) = NKA + 1 - ord(K) and WAk(W,K2) = 1),
                  If(indK = 0,
                     WAk(W,K2) = 0;
                    );
                  If(WAk(W,K2) = 1,
                     indK = 0;
                    );
                 );
            );
       );
    );


* Determine heat contents of process streams and utilities
Parameters
    QH(H,K)  heat contents of hot process streams
    QC(C,K)  heat contents of cold process streams ;

QH(H,K) = 0;
QC(C,K) = 0;

QH(H,K) = FCpH(H)*(TH(K) - max(TH(K+1), ToutH(H))) $ (Hk(H,K) = 1);
QC(C,K) = FCpC(C)*(min(TC(K), ToutC(C)) - TC(K+1)) $ (Ck(C,K) = 1);

Parameters
    QHT(H)  total heat contents of hot process streams
    QCT(C)  total heat contents of cold process streams ;

QHT(H) = FCpH(H)*(TinH(H) - ToutH(H));
QCT(C) = FCpC(C)*(ToutC(C) - TinC(C));


* Determine heat contents of process streams and utilities
Parameters
    QHA(H,K)  heat contents of hot process streams for area targeting
    QCA(C,K)  heat contents of cold process streams for area targeting ;

QHA(H,K) = 0;
QCA(C,K) = 0;

QHA(H,K) = FCpH(H)*(THA(K) - max(THA(K+1), ToutH(H))) $ (HAk(H,K) = 1);
QCA(C,K) = FCpC(C)*(min(TCA(K), ToutC(C)) - TCA(K+1)) $ (CAk(C,K) = 1);


* Define upper and lower bounds for exchanged heat load
Parameters
    QHCLO(H,C,K)  lower boounds of heat exchange between hot streams and cold streams at intervals
    QSCLO(S,C,K)  lower boounds of heat exchange between hot utilities and cold streams at intervals
    QHWLO(H,W,K)  lower boounds of heat exchange between hot streams and cold utilities at intervals
    QHCUP(H,C,K)  upper boounds of heat exchange between hot streams and cold streams at intervals
    QSCUP(S,C,K)  upper boounds of heat exchange between hot utilities and cold streams at intervals
    QHWUP(H,W,K)  upper boounds of heat exchange between hot streams and cold utilities at intervals ;

    QHCLO(H,C,K) = 0;
    QSCLO(S,C,K) = 0;
    QHWLO(H,W,K) = 0;
    QHCUP(H,C,K) = +inf;
    QSCUP(S,C,K) = +inf;
    QHWUP(H,W,K) = +inf;

* Define heat residuals
Parameter
    R(K)  total heat residual exiting temperature intervals ;

    R(K) = 0;

Scalars
    Time_LP  solution time for LP model   / 0 /
    Time_MILP  solution time for MILP model   / 0 / ;


* Define variables
Positive Variables
    QS(S)  heat load of hot utilities
    QW(W)  heat load of cold utilities ;

Positive Variable
    QSR(S)  real heat load of hot utilities ;

Positive Variables
    QHC(H,C,K)  exchange of heat of hot streams and cold streams at intervals
    QSC(S,C,K)  exchange of heat of hot utilities and cold streams at intervals
    QHW(H,W,K)  exchange of heat of hot streams and cold utilities at intervals
    RH(H,K)  heat residual of hot streams exiting intervals
    RS(S,K)  heat residual of hot utilities exiting intervals ;

    RH.fx(H,K)$(ord(K)=NK) = 0;

    QHC.lo(H,C,K) = QHCLO(H,C,K);
    QHC.up(H,C,K) = QHCUP(H,C,K);
    QSC.lo(S,C,K) = QSCLO(S,C,K);
    QSC.up(S,C,K) = QSCUP(S,C,K);
    QHW.lo(H,W,K) = QHWLO(H,W,K);
    QHW.up(H,W,K) = QHWUP(H,W,K);

Positive Variables
    qHCKM(H,C,K,K2)  disaggregated QHC
    qSCKM(S,C,K,K2)  disaggregated QSC
    qHWKM(H,W,K,K2)  disaggregated QHW ;

Variable
    Z  objective function for utility targeting
    ZA  objective function for area targeting ;


* Define equations
Equations
    Obj  objective function for utility targeting ;

    Obj..  Z =e= sum(S, CS(S)*QSR(S)) + sum(W, CW(W)*QW(W));

Equations
    ObjA  objective function for area targeting ;

    ObjA..  ZA =e= sum( (K,K2)$(ord(K)<=NKA and ord(K2)<=NKA and ord(K2)>=ord(K)),
                        1/(Ft*LMTD(K,K2)) * ( sum((H,C)$(HAk(H,K)=1 and CAk(C,K2)=1), qHCKM(H,C,K,K2)*(1/hH(H) + 1/hC(C)))
                                            + sum((S,C)$(SAk(S,K)=1 and CAk(C,K2)=1), qSCKM(S,C,K,K2)*(1/hS(S) + 1/hC(C)))
                                            + sum((H,W)$(HAk(H,K)=1 and WAk(W,K2)=1), qHWKM(H,W,K,K2)*(1/hH(H) + 1/hW(W)))
                                            - sum((S,CF)$(SAk(S,K)=1 and CAk(CF,K2)=1), qSCKM(S,CF,K,K2)*(1/hS(S) + 1/hC(CF))) ) );

Equations
    HeatBalH(H,K)  heat balance of hot streams at intervals
    HeatBalS(S,K)  heat balance of hot utilities at intervals
    HeatBalC(C,K)  heat balance of cold streams at intervals
    HeatBalW(W,K)  heat balance of cold utilities at intervals ;

    HeatBalH(H,K) $ (Hkp(H,K) = 1) ..
        RH(H,K) - RH(H,K-1)$(Hkp(H,K-1)=1) + sum(C$(Ck(C,K)=1), QHC(H,C,K))
            + sum(W$(Wk(W,K)=1), QHW(H,W,K)) =e= QH(H,K);

    HeatBalS(S,K) $ (Skp(S,K) = 1) ..
        RS(S,K) - RS(S,K-1)$(Skp(S,K-1)=1) + sum(C$(Ck(C,K)=1), QSC(S,C,K))
            - QS(S)$(Sk(S,K)=1) =e= 0;

    HeatBalC(C,K) $ (Ck(C,K) = 1) ..
        sum(H$(Hkp(H,K)=1), QHC(H,C,K)) + sum(S$(Skp(S,K)=1), QSC(S,C,K))
            =e= QC(C,K);

    HeatBalW(W,K) $ (Wk(W,K) = 1) ..
        sum(H$(Hkp(H,K)=1), QHW(H,W,K)) - QW(W) =e= 0;

Equations
    DisHeatBalH(H,K)  disaggregated heat balance of hot streams at intervals
    DisHeatBalS(S,K)  disaggregated heat balance of hot utilities at intervals
    DisHeatBalC(C,K)  disaggregated heat balance of cold streams at intervals
    DisHeatBalW(W,K)  disaggregated heat balance of cold utilities at intervals ;

    DisHeatBalH(H,K) $ (HAk(H,K) = 1) ..
        QHA(H,K) =e= sum((K2,C)$(ord(K2)>=ord(K) and CAk(C,K2)=1), qHCKM(H,C,K,K2))
                   + sum((K2,W)$(ord(K2)>=ord(K) and WAk(W,K2)=1), qHWKM(H,W,K,K2));

    DisHeatBalS(S,K) $ (SAk(S,K) = 1) ..
        QS(S) =e= sum((K2,C)$(ord(K2)>=ord(K) and CAk(C,K2)=1), qSCKM(S,C,K,K2));

    DisHeatBalC(C,K) $ (CAk(C,K) = 1) ..
        QCA(C,K) =e= sum((K2,H)$(ord(K2)<=ord(K) and HAk(H,K2)=1), qHCKM(H,C,K2,K))
                   + sum((K2,S)$(ord(K2)<=ord(K) and SAk(S,K2)=1), qSCKM(S,C,K2,K));

    DisHeatBalW(W,K) $ (WAk(W,K) = 1) ..
        QW(W) =e= sum((K2,H)$(ord(K2)<=ord(K) and HAk(H,K2)=1), qHWKM(H,W,K2,K));

Equations
    QSRQS(S)     relations between QSR and QS
    DisQSRQS(S)  disaggreagated relations between QSR and QS ;

    QSRQS(S) ..
        QSR(S) =e= QS(S) - sum((CF,K)$(Skp(S,K)=1 and Ck(CF,K)=1), QSC(S,CF,K));

    DisQSRQS(S) ..
        QSR(S) =e= QS(S) - sum((CF,K,K2)$(SAk(S,K)=1 and CAk(CF,K2)=1 and ord(K2)>=ord(K)), qSCKM(S,CF,K,K2));


Model Transshipment  / Obj, HeatBalH, HeatBalS, HeatBalC, HeatBalW, QSRQS /;

Model Transportion  / ObjA, DisHeatBalH, DisHeatBalS, DisHeatBalC, DisHeatBalW, DisQSRQS /;


* Start solving LP Transtripment model with re-calculation for cooling water outlet temperatures

* Solve LP Transtripment model for the minimum uitility consumption
Solve Transshipment minimizing Z using LP;

Time_LP = Time_LP + Transshipment.resusd;

* Fixing utility results from LP transshipment model
QS.fx(S) = QS.l(S);
QW.fx(W) = QW.l(W);
QSR.fx(S) = QSR.l(S);

* Solve LP Transportation model for the minimum uitility consumption
Solve Transportion minimizing ZA using LP;

Time_LP = Time_LP + Transportion.resusd;

Display QS.l, QSR.l, QW.l, Z.l, ZA.l, Time_LP;


Parameters
    QFH(C)  heat addition to feed water heaters ;

    QFH(C) = 0;
    QFH(CF) = sum((H,K)$(Hkp(H,K)=1 and Ck(CF,K)=1), QHC.l(H,CF,K));

Set Rank  set for ranking or ordering  / 1*5 / ;


file fout  / GamsOutput.txt /;
put fout;
put Z.l:16:4/;
put ZA.l:16:4/;
Loop(S,
     put QSR.l(S):16:4/;
    );
Loop(W,
     put QW.l(W):16:4/;
    );
If(card(CF) >= 1,
   Loop(Rank,
        Loop(CF,
             If(RankCF(CF) = ord(Rank),
                put QFH(CF):16:4/;
               );
            );
       );
  );
putclose;
