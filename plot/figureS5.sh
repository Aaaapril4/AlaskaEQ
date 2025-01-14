#!/bin/bash
gmt --version
gmt gmtset MAP_FRAME_TYPE fancy
gmt gmtset MAP_FRAME_WIDTH 3p
gmt gmtset FONT 10p,Times-Roman
gmt gmtset FONT_LABEL 10p, Times-Romans
gmt gmtset PS_MEDIA a3
gmt gmtset MAP_TITLE_OFFSET 1p
gmt gmtset MAP_LABEL_OFFSET 1p
gmt gmtset MAP_ANNOT_OFFSET 2p
gmt gmtset MAP_TICK_LENGTH_PRIMARY 2p
gmt gmtset MAP_TICK_LENGTH_SECONDARY 1p
gmt gmtset MAP_TICK_PEN_PRIMARY 1p
gmt gmtset MAP_TICK_PEN_SECONDARY 0.5p
gmt gmtset MAP_FRAME_PEN 1p
R=-162/-155/53/57
J=m0.4i
range=30
PS=figureS5.ps

slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
numf_sandpoint=/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2/sandpoint_100
numf_chignik=/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2/chignik_20
numf_simeonof=/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2/simeonof_20
cmtf=/mnt/home/jieyaqi/code/AlaskaEQ/data/cmt.csv
bdlst2=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/pb2002_steps.dat
coast=100

# plot accumulated number of events
size=7
R1=-100/200/0/200 # histogram
R2=-100/200/0/1500 # line
J1=X3.2i/0.8i
J2=X3.2i/0.8i
R3=-100/200/-40/40
J3=X3.2i/-0.5i

# #e02514 normal #4e00f5 thrust #40a362 strike #90643B normalstrike #4752ac thruststrike

gmt psxy -R$R3 -J$J3 -W1p,lightgray,- -K -Y8i > $PS << EOF
-200 0
600 0
EOF
awk -F, '$15!="" && NR>1 {print $15, $17, $3, $4, $5, $6, $7, $8, $9, $10, $15, $17}' $cmtf |\
gmt psmeca -J$J3 -R$R3 -Sm"$size"p -Gdarkgray -T -K -O >> $PS
# awk -F, '$20 && $17 && NR>1 {print $17, $27, $4, $20, $21, $22, $23, $24, $25, $26, $17, $27}' $seisf |\
# gmt psmeca -J$J3 -R$R3 -Sm"$size"p -G#4e00f5 -K -O >> $PS

# awk -F, '$13=="thrust"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, $17 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#4e00f5 -K -O >> $PS
# awk -F, '$13=="thrust"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, $17 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#4e00f5 -K -O >> $PS
# awk -F, '$13=="normalstrike"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, $17 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#90643B -K -O >> $PS
# awk -F, '$13=="thruststrike"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, $17 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#4752ac -K -O >> $PS
# awk -F, '$13=="normal"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, $17 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#e02514  -K -O  >> $PS
gmt psbasemap -R$R3 -J$J3 -By40f10 -BWe -By+l'Dist_slab' -K -O >> $PS

awk -F, '{print $1, $2, 0.004}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $5}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "overriding plate (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx100f50 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1500f300 -BE -K -O >> $PS

awk -F, '{print $1, $4, 0.004}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $6}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx100f50 -BWs -By+l'# Events per day' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1500f300 -BE -K -O >> $PS

awk -F, '{print $1, $3, 0.004}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "intraslab (dist<-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx100f50 -BWS -K -O -Bx+l'Days after Sand Point' >> $PS
gmt psbasemap -R$R2 -J$J2 -By1500f300 -BE -K -O >> $PS


R1=-5/30/0/200 # histogram
R2=-5/30/0/1000 # line
J1=X3.2i/0.8i
J2=X3.2i/0.8i
R3=-5/30/-40/40
J3=X3.2i/-0.5i

# # #e02514 normal #4e00f5 thrust #40a362 strike #90643B normalstrike #4752ac thruststrike
gmt psxy -R$R3 -J$J3 -W1p,lightgray,- -K -O -X4i -Y2.7i >> $PS << EOF
-5 0
30 0
EOF
awk -F, '$15!="" && NR>1 {print $15, $17, $3, $4, $5, $6, $7, $8, $9, $10, $15, $17}' $cmtf |\
gmt psmeca -J$J3 -R$R3 -Sm"$size"p -T -Gdarkgray -K -O >> $PS
# awk -F, '$20 && $17 && NR>1 {print $17, $27, $4, $20, $21, $22, $23, $24, $25, $26, $17, $27}' $seisf |\
# gmt psmeca -J$J3 -R$R3 -Sm"$size"p -G#4e00f5 -K -O >> $PS

# awk -F, '$13=="thrust"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, 1 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#4e00f5 -K -O >> $PS
# awk -F, '$13=="normalstrike"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, 1 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#90643B -K -O >> $PS
# awk -F, '$13=="thruststrike"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, 1 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#4752ac -K -O >> $PS
# awk -F, '$13=="normal"{print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $11, $16, 1 }' $cmtf| \
# gmt psmeca -J$J3 -R$R3 -Sc"$size"p -G#e02514 -K -O  >> $PS
gmt psbasemap -R$R3 -J$J3 -By40f10 -BEw -By+l'Dist_slab' -K -O >> $PS


awk -F, '{print $1, $2, 0.008}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $5}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "overriding plate (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWs  -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS

awk -F, '{print $1, $4, 0.008}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -By+l'# Accumulated Events' -K -O >> $PS

awk -F, '{print $1, $3, 0.008}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $6}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "intraslab (dist<-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWS -Bx+l'Days after Sand Point' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS


# plot accumulated number of events
size=7
R1=-20/60/0/200 # histogram
R2=-20/60/0/2000 # line
J1=X3.2i/0.8i
J2=X3.2i/0.8i
R3=-20/60/-40/40
J3=X3.2i/-0.5i

gmt psxy -R$R3 -J$J3 -W1p,lightgray,- -K -O -X-4i -Y-1i >> $PS << EOF
-200 0
600 0
EOF
awk -F, '$14!="" && NR>1 {print $14, $17, $3, $4, $5, $6, $7, $8, $9, $10, $14, $17}' $cmtf |\
gmt psmeca -J$J3 -R$R3 -Sm"$size"p -Gdarkgray -T -K -O >> $PS
gmt psbasemap -R$R3 -J$J3 -By40f10 -BWe -By+l'Dist_slab' -K -O >> $PS

awk -F, '{print $1, $2, 0.008}' $numf_simeonof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $5}' $numf_simeonof | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "overriding plate (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWs  -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS

awk -F, '{print $1, $4, 0.008}' $numf_simeonof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_simeonof | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWs -By+l'# Events per day' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS

awk -F, '{print $1, $3, 0.008}' $numf_simeonof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $6}' $numf_simeonof | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "intraslab (dist<-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWS -Bx+l'Days after Simeonof' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By1000f200 -BE -K -O >> $PS


size=7
R1=-20/60/0/200 # histogram
R2=-20/60/0/400 # line
J1=X3.2i/0.8i
J2=X3.2i/0.8i
R3=-20/60/-40/40
J3=X3.2i/-0.5i

gmt psxy -R$R3 -J$J3 -W1p,lightgray,- -K -O -X4i -Y2.7i >> $PS << EOF
-200 0
600 0
EOF
awk -F, '$16!="" && NR>1 {print $16, $17, $3, $4, $5, $6, $7, $8, $9, $10, $16, $17}' $cmtf |\
gmt psmeca -J$J3 -R$R3 -Sm"$size"p -Gdarkgray -T -K -O >> $PS
gmt psbasemap -R$R3 -J$J3 -By40f10 -BEw -By+l'Dist_slab' -K -O >> $PS

awk -F, '{print $1, $2, 0.008}' $numf_chignik | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray  -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $5}' $numf_chignik | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "overriding plate (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWs  -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By400f100 -BE -K -O >> $PS

awk -F, '{print $1, $4, 0.008}' $numf_chignik | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_chignik | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By400f100 -BE -By+l'# Accumulated Events' -K -O >> $PS

awk -F, '{print $1, $3, 0.008}' $numf_chignik | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-0.9i -K -O >> $PS
awk -F, '{print $1, $6}' $numf_chignik | gmt psxy -R$R2 -J$J2 -W1p,"#4E00F5" -K -O >> $PS
echo "intraslab (dist<-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By200f40 -Bx5f1 -BWS -Bx+l'Days after Chignik' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By400f100 -BE -K -O >> $PS


gmt psconvert -A -P -Tf $PS
rm gmt.*
rm topo.grd
rm $PS