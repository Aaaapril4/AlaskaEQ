#!/bin/bash
gmt --version
gmt gmtset MAP_FRAME_TYPE fancy
gmt gmtset MAP_FRAME_WIDTH 3p
gmt gmtset FONT 10p,Helvetica
gmt gmtset FONT_LABEL 10p,Helvetica
gmt gmtset PS_MEDIA a3
gmt gmtset MAP_TITLE_OFFSET 1p
gmt gmtset MAP_LABEL_OFFSET 1p
gmt gmtset MAP_ANNOT_OFFSET 2p
gmt gmtset MAP_TICK_LENGTH_PRIMARY 2p
gmt gmtset MAP_TICK_LENGTH_SECONDARY 1p
gmt gmtset MAP_TICK_PEN_PRIMARY 1p
gmt gmtset MAP_TICK_PEN_SECONDARY 0.5p
gmt gmtset MAP_FRAME_PEN 1p
PS=figure6.ps

slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
numf_sandpoint=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/sandpoint.csv
numf_chignik=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/chignik.csv
numf_simeonof=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/simeonof.csv
numf_sandpoint2023=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/sandpoint2023.csv
cmtf=/mnt/home/jieyaqi/code/AlaskaEQ/data/cmt_all.csv
size=7
#region Simeonof
# plot accumulated number of events
R1=-8000/500/0/20 # histogram
R2=-8000/500/0/3000 # line
R3=-8000/500/0/0.2 # line
J1=X3.2i/0.9i
J2=X3.2i/0.9i
J3=X3.2i/0.9i
R4=-8000/500/-40/40
J4=X3.2i/-0.5i

# XO start -802.2588366898148 end -204.25883668981479

gmt psxy -R$R4 -J$J4 -W1p,lightgray,- -K -Y8i > $PS << EOF
-8000 0
100 0
EOF
awk -F, '$14 && $18 && NR>1 {print $14, $18, $3, $4, $5, $6, $7, $8, $9, $10, $14, $18}' $cmtf |\
gmt psmeca -J$J4 -R$R4 -Sm"$size"p -Gdarkgray -T -K -O >> $PS
echo "a)" | gmt pstext -R$R4 -J$J4 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R4 -J$J4 -By40f10 -BWe -By+l'Slab-normal Distance (km)' -K -O >> $PS

awk -F, '{print $1, $2, 0.0026}' $numf_simeonof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $6}' $numf_simeonof | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$9{print $1, $9}' $numf_simeonof | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "overriding plate (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-802.2588366898148 0
-204.25883668981479 0
-204.25883668981479 20
-802.2588366898148 20
-802.2588366898148 0
EOF
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -Byy1000f200 -BE -K -O >> $PS


awk -F, '{print $1, $3, 0.0026}' $numf_simeonof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_simeonof | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$10{print $1, $10}' $numf_simeonof | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-802.2588366898148 0
-204.25883668981479 0
-204.25883668981479 20
-802.2588366898148 20
-802.2588366898148 0
EOF
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -By+l'# Events per day' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -Byy1000f200 -BE -K -O >> $PS

awk -F, '{print $1, $4, 0.0026}' $numf_simeonof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $8}' $numf_simeonof | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$11{print $1, $11}' $numf_simeonof | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "intraslab (dist<-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-802.2588366898148 0
-204.25883668981479 0
-204.25883668981479 20
-802.2588366898148 20
-802.2588366898148 0
EOF
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWS -K -O -Bx+l'Days after 2020 Mw7.8 Simeonof' >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS
#endregion

#region Sandpoint
maxh=8
# plot accumulated number of events
R1=-8000/500/0/$maxh # histogram
R2=-8000/500/0/300
R3=-8000/500/0/0.2 # line
J1=X3.2i/0.9i
J2=X3.2i/0.9i
J3=X3.2i/0.9i
R4=-8000/500/-40/40
J4=X3.2i/-0.5i

# XO start -891.871292824074 end -293.8712928240741 simeonof -89.61245613425926

gmt psxy -R$R4 -J$J4 -W1p,lightgray,- -K -O -X4i -Y3i >> $PS << EOF
-8000 0
100 0
EOF
awk -F, '$15 && $18 && NR>1 {print $15, $18, $3, $4, $5, $6, $7, $8, $9, $10, $15, $18}' $cmtf |\
gmt psmeca -J$J4 -R$R4 -Sm"$size"p -Gdarkgray -T -K -O >> $PS
echo "b)" | gmt pstext -R$R4 -J$J4 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R4 -J$J4 -By40f10 -BwE -By+l'Slab-Normal Distance (km)' -K -O >> $PS

awk -F, '{print $1, $2, 0.0026}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i  -K -O >> $PS
awk -F, '{print $1, $6}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$9{print $1, $9}' $numf_sandpoint | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "overriding plate (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-891.871292824074 0
-293.8712928240741 0
-293.8712928240741 $maxh
-891.871292824074 $maxh
-891.871292824074 0
EOF
echo -89.61245613425926 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
gmt psbasemap -R$R1 -J$J1 -By4f1 -Bx2000f500 -BWs  -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By100f20 -BE -K -O >> $PS

awk -F, '{print $1, $3, 0.0026}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$10{print $1, $10}' $numf_sandpoint | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-891.871292824074 0
-293.8712928240741 0
-293.8712928240741 $maxh
-891.871292824074 $maxh
-891.871292824074 0
EOF
echo -89.61245613425926 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
gmt psbasemap -R$R1 -J$J1 -By4f1 -Bx2000f500 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By100f20 -BE -By+l'# Accumulated Events' -K -O >> $PS

awk -F, '{print $1, $4, 0.0026}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $8}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$11{print $1, $11}' $numf_sandpoint | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "intraslab (dist<-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-891.871292824074 0
-293.8712928240741 0
-293.8712928240741 $maxh
-891.871292824074 $maxh
-891.871292824074 0
EOF
echo -89.61245613425926 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
gmt psbasemap -R$R1 -J$J1 -By4f1 -Bx2000f500 -BWS -Bx+l'Days after 2020 Mw 7.6 Sand Point' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By100f20 -BE -K -O >> $PS
#endregion

#region Chignik
maxh=20
R1=-8000/500/0/$maxh # histogram
R2=-8000/500/0/3000
R3=-8000/500/0/0.2 # line
J1=X3.2i/0.9i
J2=X3.2i/0.9i
J3=X3.2i/0.9i
R4=-8000/500/-40/40
J4=X3.2i/-0.5i

# XO start -1174.2609663194444 end -576.2609663194445 simeonof -372.00212962962956

gmt psxy -R$R4 -J$J4 -W1p,lightgray,- -K -O  -X-4i -Y-1.5i >> $PS << EOF
-8000 0
100 0
EOF
awk -F, '$16 && $18 && NR>1 {print $16, $18, $3, $4, $5, $6, $7, $8, $9, $10, $16, $18}' $cmtf |\
gmt psmeca -J$J4 -R$R4 -Sm"$size"p -Gdarkgray -T -K -O >> $PS
echo "c)" | gmt pstext -R$R4 -J$J4 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R4 -J$J4 -By40f10 -BWe -By+l'Slab-Normal Distance (km)' -K -O >> $PS

awk -F, '{print $1, $2, 0.0026}' $numf_chignik | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $6}' $numf_chignik | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$9{print $1, $9}' $numf_chignik | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "overriding plate (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-1174.2609663194444 0
-576.2609663194445 0
-576.2609663194445 $maxh
-1174.2609663194444 $maxh
-1174.2609663194444 0
EOF
echo -372.00212962962956 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs  -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS

awk -F, '{print $1, $3, 0.0026}' $numf_chignik | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_chignik | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$10{print $1, $10}' $numf_chignik | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-1174.2609663194444 0
-576.2609663194445 0
-576.2609663194445 $maxh
-1174.2609663194444 $maxh
-1174.2609663194444 0
EOF
echo -372.00212962962956 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50  >> $PS
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -By+l'# Events per day' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS

awk -F, '{print $1, $4, 0.0026}' $numf_chignik | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $8}' $numf_chignik | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$11{print $1, $11}' $numf_chignik | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "intraslab (dist<-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-1174.2609663194444 0
-576.2609663194445 0
-576.2609663194445 $maxh
-1174.2609663194444 $maxh
-1174.2609663194444 0
EOF
echo -372.00212962962956 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50  >> $PS
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWS -Bx+l'Days after 2021 Mw 8.2 Chignik' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS
#endregion

#region Sandpoint2023
maxh=20
# plot accumulated number of events
R1=-8000/500/0/$maxh # histogram
R2=-8000/500/0/8000
R3=-8000/500/0/0.2 # line
J1=X3.2i/0.9i
J2=X3.2i/0.9i
J3=X3.2i/0.9i
R4=-8000/500/-40/40
J4=X3.2i/-0.5i

# XO start -1891.2835782175925 end -1293.2835782175928 simeonof -1089.0247415277777 chignik -717.022611898148

gmt psxy -R$R4 -J$J4 -W1p,lightgray,- -K -O -X4i -Y3i >> $PS << EOF
-8000 0
100 0
EOF
awk -F, '$17 && $18 && NR>1 {print $17, $18, $3, $4, $5, $6, $7, $8, $9, $10, $17, $18}' $cmtf |\
gmt psmeca -J$J4 -R$R4 -Sm"$size"p -Gdarkgray -T -K -O >> $PS
echo "d)" | gmt pstext -R$R4 -J$J4 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R4 -J$J4 -By40f10 -BwE -By+l'Slab-Normal Distance (km)' -K -O >> $PS

awk -F, '{print $1, $2, 0.0026}' $numf_sandpoint2023 | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $6}' $numf_sandpoint2023 | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$9{print $1, $9}' $numf_sandpoint2023 | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "overriding plate (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-1891.2835782175925 0
-1293.2835782175928 0
-1293.2835782175928 $maxh
-1891.2835782175925 $maxh
-1891.2835782175925 0
EOF
echo -1089.0247415277777 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
echo -717.022611898148 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs  -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By2000f200 -BE -K -O >> $PS

awk -F, '{print $1, $3, 0.0026}' $numf_sandpoint2023 | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_sandpoint2023 | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$10{print $1, $10}' $numf_sandpoint2023 | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-1891.2835782175925 0
-1293.2835782175928 0
-1293.2835782175928 $maxh
-1891.2835782175925 $maxh
-1891.2835782175925 0
EOF
echo -1089.0247415277777 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
echo -717.022611898148 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By2000f200 -BE  -By+l'# Accumulated Events' -K -O >> $PS

awk -F, '{print $1, $4, 0.0026}' $numf_sandpoint2023 | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1i -K -O >> $PS
awk -F, '{print $1, $8}' $numf_sandpoint2023 | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$11{print $1, $11}' $numf_sandpoint2023 | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "intraslab (dist<-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
-1891.2835782175925 0
-1293.2835782175928 0
-1293.2835782175928 $maxh
-1891.2835782175925 $maxh
-1891.2835782175925 0
EOF
echo -1089.0247415277777 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
echo -717.022611898148 $maxh 0  | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWS -Bx+l'Days after 2023 Mw 7.2 Sand Point' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By2000f200 -BE -K -O >> $PS
#endregion



gmt psconvert -A -P -Tf $PS
rm gmt.*
rm $PS