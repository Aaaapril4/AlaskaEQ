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
PS=figure7.ps

numf_pavlof=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/pavlof.csv
numf_veniaminof=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/veniaminof.csv
numf_aniakchak=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/aniakchak.csv
numf_trident=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/trident.csv


#region Pavlof
size=7
R1=-8000/100/0/5 # histogram
R2=-8000/100/0/500 # line
R3=-8000/100/0/0.002 # line
J1=X4i/1.1i
J2=X4i/1.1i
J3=X4i/1.1i

# XO start -802.2588366898148 end -204.25883668981479
awk -F, '{print $1, $2, 0.0005}' $numf_pavlof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y8i -K > $PS
awk -F, '{print $1, $4}' $numf_pavlof | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$5{print $1, $5}' $numf_pavlof | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "Pavlof" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
# gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
# -802.2588366898148 0
# -204.25883668981479 0
# -204.25883668981479 20
# -802.2588366898148 20
# -802.2588366898148 0
# EOF
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By800f200 -BE -K -O >> $PS
#endregion


#region Pavlof
size=7
R1=-8000/100/0/5 # histogram
R2=-8000/100/0/500 # line
R3=-8000/100/0/0.002 # line
J1=X4i/1.1i
J2=X4i/1.1i
J3=X4i/1.1i

# XO start -802.2588366898148 end -204.25883668981479
awk -F, '{print $1, $2, 0.0005}' $numf_veniaminof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1.3i -K -O >> $PS
awk -F, '{print $1, $4}' $numf_veniaminof| gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$5{print $1, $5}' $numf_veniaminof | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "Veniaminof" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
# gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
# -802.2588366898148 0
# -204.25883668981479 0
# -204.25883668981479 20
# -802.2588366898148 20
# -802.2588366898148 0
# EOF
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By800f200 -BE -K -O >> $PS
#endregion


#region Pavlof
size=7
R1=-8000/100/0/10 # histogram
R2=-8000/100/0/500 # line
R3=-8000/100/0/0.004 # line
J1=X4i/1.1i
J2=X4i/1.1i
J3=X4i/1.1i

# XO start -802.2588366898148 end -204.25883668981479
awk -F, '{print $1, $2, 0.0005}' $numf_aniakchak | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1.3i -K -O >> $PS
awk -F, '{print $1, $4}' $numf_aniakchak| gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$5{print $1, $5}' $numf_aniakchak | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "Aniakchak" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
# gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
# -802.2588366898148 0
# -204.25883668981479 0
# -204.25883668981479 20
# -802.2588366898148 20
# -802.2588366898148 0
# EOF
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By800f200 -BE -K -O >> $PS
#endregion


#region Pavlof
size=7
R1=-8000/100/0/30 # histogram
R2=-8000/100/0/6000 # line
R3=-8000/100/0/0.2 # line
J1=X4i/1.1i
J2=X4i/1.1i
J3=X4i/1.1i

# XO start -802.2588366898148 end -204.25883668981479
awk -F, '{print $1, $2, 0.0005}' $numf_trident | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1.3i -K -O >> $PS
awk -F, '{print $1, $4}' $numf_trident| gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$5{print $1, $5}' $numf_trident | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "Trident" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
# gmt psxy -R$R1 -J$J1 -W0.1p,yellow -Gyellow -t90 -K -O << EOF >> $PS
# -802.2588366898148 0
# -204.25883668981479 0
# -204.25883668981479 20
# -802.2588366898148 20
# -802.2588366898148 0
# EOF
gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By800f200 -BE -K -O >> $PS
#endregion

gmt psconvert -A -P -Tf $PS
rm gmt.*
rm $PS