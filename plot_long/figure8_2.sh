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
PS=figure8_2.ps

numf_pavlof=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/pavlof.csv
numf_veniaminof=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/veniaminof.csv
numf_aniakchak=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/aniakchak.csv
numf_trident=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/trident.csv
activity=../data/activity.csv

# #region Pavlof
# maxh=5
# R1=-8000/100/0/$maxh # histogram
# R2=-8000/100/0/800 # line
# R3=-8000/100/0/0.004 # line
# J1=X4i/1.1i
# J2=X4i/1.1i
# J3=X4i/1.1i

# awk -F, '{print $1, $2, 0.0005}' $numf_pavlof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y8i -K > $PS
# awk -F, '{print $1, $4}' $numf_pavlof | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
# awk -F, '$5{print $1, $5}' $numf_pavlof | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
# echo "Pavlof" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS

# awk -F, '
# {
#   if ($1 == "Pavlof" && $5 != "" && $6 == "eruption") {
#     print $4, "0"
#     print $5, "0"
#     print $5, "'$maxh'"
#     print $4, "'$maxh'"
#     print $4, "0"
#     print ">"
#   }
# }' $activity |\
# gmt psxy -R$R1 -J$J1 -W0.1p,pink -Gpink -t80 -K -O >> $PS
# awk -F, '
# {
#   if ($1 == "Pavlof" && $5 != "" && $6 == "") {
#     print $4, "0"
#     print $5, "0"
#     print $5, "'$maxh'"
#     print $4, "'$maxh'"
#     print $4, "0"
#     print ">"
#   }
# }' $activity |\
# gmt psxy -R$R1 -J$J1 -W0.1p,black -Gblack -t90 -K -O >> $PS
# awk -F, '$1 == "Pavlof" && $5 == "" && $6 == "eruption" {print $4, "'$maxh'", 0}' $activity | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gpink -K -O -t50 >> $PS
# awk -F, '$1 == "Pavlof" && $5 == "" && $6 == "" {print $4, "'$maxh'", 0}' $activity | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS

# gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
# gmt psbasemap -R$R2 -J$J2 -By800f200 -BE -K -O >> $PS
# #endregion


# #region Veniaminof
# maxh=5
# R1=-8000/100/0/$maxh # histogram
# R2=-8000/100/0/500 # line
# R3=-8000/100/0/0.004 # line
# J1=X4i/1.1i
# J2=X4i/1.1i
# J3=X4i/1.1i

# # XO start -802.2588366898148 end -204.25883668981479
# awk -F, '{print $1, $2, 0.0005}' $numf_veniaminof | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1.3i -K -O >> $PS
# awk -F, '{print $1, $4}' $numf_veniaminof| gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
# awk -F, '$5{print $1, $5}' $numf_veniaminof | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
# echo "Veniaminof" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS

# awk -F, '
# {
#   if ($1 == "Veniaminof" && $5 != "" && $6 == "eruption") {
#     print $4, "0"
#     print $5, "0"
#     print $5, "'$maxh'"
#     print $4, "'$maxh'"
#     print $4, "0"
#     print ">"
#   }
# }' $activity |\
# gmt psxy -R$R1 -J$J1 -W0.1p,pink -Gpink -t80 -K -O >> $PS
# awk -F, '
# {
#   if ($1 == "Veniaminof" && $5 != "" && $6 == "") {
#     print $4, "0"
#     print $5, "0"
#     print $5, "'$maxh'"
#     print $4, "'$maxh'"
#     print $4, "0"
#     print ">"
#   }
# }' $activity |\
# gmt psxy -R$R1 -J$J1 -W0.1p,black -Gblack -t90 -K -O >> $PS
# awk -F, '$1 == "Veniaminof" && $5 == "" && $6 == "eruption" {print $4, "'$maxh'", 0}' $activity | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gpink -K -O -t50 >> $PS
# awk -F, '$1 == "Veniaminof" && $5 == "" && $6 == "" {print $4, "'$maxh'", 0}' $activity | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS

# gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
# gmt psbasemap -R$R2 -J$J2 -By800f200 -BE -K -O >> $PS
# #endregion


# #region Aniakchak
# maxh=10
# R1=-8000/100/0/$maxh # histogram
# R2=-8000/100/0/800 # line
# R3=-8000/100/0/0.006 # line
# J1=X4i/1.1i
# J2=X4i/1.1i
# J3=X4i/1.1i

# awk -F, '{print $1, $2, 0.0005}' $numf_aniakchak | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1.3i -K -O >> $PS
# awk -F, '{print $1, $4}' $numf_aniakchak| gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
# awk -F, '$5{print $1, $5}' $numf_aniakchak | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
# echo "Aniakchak" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS

# awk -F, '
# {
#   if ($1 == "Aniakchak" && $5 != "" && $6 == "eruption") {
#     print $4, "0"
#     print $5, "0"
#     print $5, "'$maxh'"
#     print $4, "'$maxh'"
#     print $4, "0"
#     print ">"
#   }
# }' $activity |\
# gmt psxy -R$R1 -J$J1 -W0.1p,pink -Gpink -t80 -K -O >> $PS
# awk -F, '
# {
#   if ($1 == "Aniakchak" && $5 != "" && $6 == "") {
#     print $4, "0"
#     print $5, "0"
#     print $5, "'$maxh'"
#     print $4, "'$maxh'"
#     print $4, "0"
#     print ">"
#   }
# }' $activity |\
# gmt psxy -R$R1 -J$J1 -W0.1p,black -Gblack -t90 -K -O >> $PS
# awk -F, '$1 == "Aniakchak" && $5 == "" && $6 == "eruption" {print $4, "'$maxh'", 0}' $activity | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gpink -K -O -t50 >> $PS
# awk -F, '$1 == "Aniakchak" && $5 == "" && $6 == "" {print $4, "'$maxh'", 0}' $activity | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gblack -K -O -t50 >> $PS

# gmt psbasemap -R$R1 -J$J1 -By10f2 -Bx2000f500 -BWs -K -O >> $PS
# gmt psbasemap -R$R2 -J$J2 -By800f200 -BE -K -O >> $PS
# #endregion


#region Trident
maxh=30
R1=-8000/100/0/$maxh # histogram
R2=-8000/100/0/8000 # line
R3=-8000/100/0/0.3 # line
J1=X4i/1.5i
J2=X4i/1.5i
J3=X4i/1.5i

awk -F, '{print $1, $2, 0.015}' $numf_trident | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y3i -K >> $PS
awk -F, '{print $1, $4}' $numf_trident| gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
awk -F, '$5{print $1, $5}' $numf_trident | gmt psxy -R$R3 -J$J3 -W0.5p,"#6868FF" -K -O >> $PS
echo "Trident" | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS

awk -F, '
{
  if ($1 == "Trident" && $5 != "" && $6 == "eruption") {
    print $4, "0"
    print $5, "0"
    print $5, "'$maxh'"
    print $4, "'$maxh'"
    print $4, "0"
    print ">"
  }
}' $activity |\
gmt psxy -R$R1 -J$J1 -W0.1p,pink -Gpink -t80 -K -O >> $PS
awk -F, '
{
  if ($1 == "Trident" && $5 != "" && $6 == "") {
    print $4, "0"
    print $5, "0"
    print $5, "'$maxh'"
    print $4, "'$maxh'"
    print $4, "0"
    print ">"
  }
}' $activity |\
gmt psxy -R$R1 -J$J1 -W0.1p,black -Gorange -t90 -K -O >> $PS
awk -F, '$1 == "Trident" && $5 == "" && $6 == "eruption" {print $4, "'$maxh'", 0}' $activity | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gpink -K -O -t50 >> $PS
awk -F, '$1 == "Trident" && $5 == "" && $6 == "" {print $4, "'$maxh'", 0}' $activity | gmt psxy -R$R1 -J$J1 -Sb0.001b -W0.8p -Gorange -K -O -t50 >> $PS

gmt psbasemap -R$R1 -J$J1 -By10f2+l"# Events Per Day" -Bx2000f500+l"Days to 2024.1.1" -BWS -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By2000f200+l"#Accumulated Events" -BE -K -O >> $PS
#endregion

gmt psconvert -A -P -Tf $PS
rm gmt.*
rm $PS