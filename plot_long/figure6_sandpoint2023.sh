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
R=-162/-155/53/57
J=m0.4i
range=30
PS=figure6_sandpoint.ps

slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
seisf=/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2/catalogs_bootstrap_processed.csv
cmtf=../data/cmt.csv
historical=../data/relocated_historical_cmt.csv
bdlst2=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/pb2002_steps.dat
coast=100
gmt makecpt -Cjet -T-99999999/99999999 -Iz -Z > cptfile.cpt
plot_cross_section() {
    depth="$5"
    staprojdis="$6"
    range="$7"
    Xoff=$8
    Yoff=$9
    w=${10}
    e=${11}
    s=${12}
    text=${13}
    echo $1 $2 $3 $4
    gmt project -C$1/$2 -E$3/$4 -G0.025 > lined
    trench=`python3 intersect.py lined trench.dat`
    if [ -z $trench ]
    then
        trench=0
    fi

    # topography
    gmt grdtrack lined -Gtopo.grd | awk '{print $1, $2, $4}' > tomolined.dat
    echo $1 $2 0 > temp
    awk 'NR==1{print '$1', '$2', $3}' tomolined.dat >> temp
    cat tomolined.dat >> temp 
    tail -n1 tomolined.dat | awk '{print '$3', '$4', $3}' >> temp
    echo $3 $4 0 >> temp
    mv temp tomolined.dat
    python3 calculate_dist.py tomolined.dat 0 1 $1 $2 $trench> temp
    mv temp tomolined.dat
    mindist=`head -n1 tomolined.dat | awk '{print $1}'`
    maxdist=`tail -n1 tomolined.dat | awk '{print $1}'`

    # slip
    gmt grdtrack lined -G$slipdir/simeonof_slip.grd | awk '{print $1, $2, $4}' > temp
    python3 calculate_dist.py temp 0 1 $1 $2 $trench > simeonof_slip
    gmt grdtrack lined -G$slipdir/chignik_slip.grd | awk '{print $1, $2, $4}' > temp
    python3 calculate_dist.py temp 0 1 $1 $2 $trench > chignik_slip
    if (( $(echo "$mindist < -240" | bc -l) ))
    then
        mindist=-240
    fi
    if (( $(echo "$maxdist > 240" | bc -l) ))
    then
        maxdist=240
    fi

    if [[ $trench == 0 ]]
    then
        R1=0/$maxdist/0/1
        R2=0/$maxdist/0/$depth
        R3=0/$maxdist/0/5
        R2_beach=$R2
    else
        R1=$mindist/50/0/1
        R2=$mindist/50/0/$depth
        R3=$mindist/50/0/5
        x1_beach=`echo $mindist + $trench | bc -l`
        x2_beach=`echo 50 + $trench | bc -l`
        R2_beach=$x1_beach/$x2_beach/0/$depth
    fi
    J1=x0.015i/0.3i
    J2=x0.015i/-0.015i
    J3=x0.015i/0.06i
    Y=`echo $depth \* 0.015 | bc -l`
    awk '{print $1, $4*0.001}' tomolined.dat | gmt psxy -R$R1 -J$J1 -W1p -X"$Xoff"i -Y"$Yoff"i -K -O -P >> $PS
    # plot location of A-A'
    if [[ ${14} == 1 ]]
    then
        # A-A' 159.609377605-243.98422167861142
        echo -84.3748440736 0.2 | gmt psxy -R$R1 -J$J1 -Si7p -Gblack -K -O >> $PS
    fi

    gmt psbasemap -R$R1 -J$J1 -By1f0.5+l'Topo(km)' -B${w}s -K -O >> $PS
    awk '{print $1, $4}' simeonof_slip | gmt psxy -R$R3 -J$J3 -W1p,"#E02514" -K -O >> $PS
    awk '{print $1, $4}' chignik_slip | gmt psxy -R$R3 -J$J3 -W1p,"#40A362" -K -O >> $PS
    echo $text\' | gmt pstext -R$R1 -J$J1 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
    echo $text | gmt pstext -R$R1 -J$J1 -F+cTR+f13p -Dj0.03i/0i -K -O>> $PS
    gmt psbasemap -R$R3 -J$J3 -By5f1+l'Slip(m)' -Bs$e -K -O >> $PS

    awk '{print $1, $4*-0.001}' tomolined.dat | gmt psxy -R$R2 -J$J2 -W1p,darkgray -Gdarkgray -Y-"$Y"i -K -O >> $PS

    #seismicity
    /mnt/home/jieyaqi/anaconda3/envs/seis/bin/python3 staclose.py $seisf $1/$2/$3/$4 $staprojdis 1 2 $trench , > staXY

    # Sandpoint
    awk -F, '$20 && $20>=0 && $20<='$range' {print $1, $7, $20, $11, $12}' staXY | gmt psxy -R$R2 -J$J2 -Sc1p -Csandpoint.cpt -E+w0p+p0.6+cl -K -O >> $PS

    # Simeonof
    awk -F, '$19 && $19>=0 && $19<='$range' {print $1, $7, $19, $11, $12}' staXY | gmt psxy -R$R2 -J$J2 -Sc1p -Csimeonof.cpt -E+w0p+p0.6+cl -K -O >> $PS

    # Chiknik
    awk -F, '$21 && $21>=0 && $21<='$range' {print $1, $7, $21, $11, $12}' staXY | gmt psxy -R$R2 -J$J2 -Sc1p -Cchignik.cpt -E+w0p+p0.6+cl -K -O >> $PS

    # CMT
    ## Sand Point
    # awk -F, '$22 && $20 && $20<0 {print $5, $6, $7, $22, $23, $24, $25, $26, $27, $28, $1, $7, $20}' staXY |\
    # gmt pscoupe -J$J2 -R$R2_beach -Aa$1/$2/$3/$4/90/10000/0/$depth -Sm10p -Q -G#444444 -K -O >> $PS 
    awk -F, '$22 && $20>=0 && $20<='$range' {print $5, $6, $7, $22, $23, $24, $25, $26, $27, $28, $1, $7, $20}' staXY |\
    while read line
    do
        value=`echo $line | awk '{print $13}'`
        color=`python3 get_color.py $value sandpoint.cpt` 
        echo $line | awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12}'| gmt pscoupe -J$J2 -R$R2_beach -Aa$1/$2/$3/$4/90/10000/0/$depth -Sm10p -Q -G$color -K -O >> $PS 
    done

    awk -F, '$22 && $19>=0 && $19<='$range' {print $5, $6, $7, $22, $23, $24, $25, $26, $27, $28, $1, $7, $19}' staXY |\
    while read line
    do
        value=`echo $line | awk '{print $13}'`
        color=`python3 get_color.py $value simeonof.cpt` 
        echo $line | awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12}'| gmt pscoupe -J$J2 -R$R2_beach -Aa$1/$2/$3/$4/90/10000/0/$depth -Sm10p -Q -G$color -K -O >> $PS 
    done

    awk -F, '$22 && $21>=0 && $21<='$range' {print $5, $6, $7, $22, $23, $24, $25, $26, $27, $28, $1, $7, $21}' staXY |\
    while read line
    do
        value=`echo $line | awk '{print $13}'`
        color=`python3 get_color.py $value chignik.cpt` 
        echo $line | awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12}'| gmt pscoupe -J$J2 -R$R2_beach -Aa$1/$2/$3/$4/90/10000/0/$depth -Sm10p -Q -G$color -K -O >> $PS 
    done
    # background
    awk -F, '$18<0 {print $1, $7, $18}' staXY | gmt psxy -R$R2 -J$J2 -Sc2.5p -G"#444444" -t20 -K -O >> $PS
    
    #slab
    gmt grdtrack lined -Gslab_Fan.grd -T0.1 | awk '{print $1, $2, $4}' > slab.grd
    python3 calculate_dist.py slab.grd 0 1 $1 $2 $trench > temp
    mv temp slab.grd
    awk '{print $1,$4}' slab.grd | gmt psxy -R$R2 -J -W1.5p,#999999 -K -O >> $PS
    gmt psbasemap -R$R2 -J$J2 -By50f10 -Bx100f20 -B${w}${s}e -Bx+l'Distance(km)' -By+l'Depth(km)' -P -K -O >> $PS

    # rm tomolined.dat
    # rm lined
    # rm slab.grd
    # rm staXY
    # rm simeonof_slip
    # rm chignik_slip

}


# plot histogram
numf_sandpoint=/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/sandpoint2023_zoomin.csv
cmtf=/mnt/home/jieyaqi/code/AlaskaEQ/data/cmt_all.csv

size=7
R1=-5/30/0/80 # histogram
R2=-5/30/0/500 # line
J1=X3.2i/1i
J2=X3.2i/1i
R3=-5/30/-20/20
J3=X3.2i/-0.8i

# # #e02514 normal #4e00f5 thrust #40a362 strike #90643B normalstrike #4752ac thruststrike
gmt psxy -R$R3 -J$J3 -W1p,lightgray,- -K -Y4i > $PS << EOF
-5 0
30 0
EOF
awk -F, '$17 && $18 && NR>1 {print $17, $18, $3, $4, $5, $6, $7, $8, $9, $10, $17, $18}' $cmtf |\
gmt psmeca -J$J4 -R$R4 -Sm"$size"p -Gdarkgray -T -K -O >> $PS

# echo "d)" | gmt pstext -R$R3 -J$J3 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R3 -J$J3 -By20f5 -BeW -By+l'Slab-Normal Distance (km)' -K -O >> $PS


awk -F, '{print $1, $2, 0.008}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1.2i -K -O >> $PS
awk -F, '{print $1, $6}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
echo "overriding plate (dist<=-5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By20f5 -Bx5f1 -BWs  -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By250f50 -BE -K -O >> $PS

awk -F, '{print $1, $3, 0.008}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1.2i -K -O >> $PS
awk -F, '{print $1, $7}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
echo "plate interface (|dist|<5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By20f5 -Bx5f1 -By+l'# Events per day' -BWs -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By250f50 -BE -By+l'# Accumulated Events' -K -O >> $PS

awk -F, '{print $1, $4, 0.008}' $numf_sandpoint | gmt psxy -R$R1 -J$J1 -Sb1ub0 -W0.01p,darkgray -Gdarkgray -Y-1.2i -K -O >> $PS
awk -F, '{print $1, $8}' $numf_sandpoint | gmt psxy -R$R2 -J$J2 -W1p,"#FF6AAD" -K -O >> $PS
echo "intraslab (dist>=5km)" | gmt pstext -R$R1 -J$J1 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By20f5 -Bx5f1 -BWS -Bx+l'Days after Sand Point' -K -O >> $PS
gmt psbasemap -R$R2 -J$J2 -By250f50 -BE -K -O >> $PS


# plot_cross_section -159.6656 56 -159.6656 53.3 100 25 1.08 1.5 w s -999999999 0 "a) Seismicity earlier than Jun 2020" B 2 1
# plot_cross_section -160.2 54.5646 -159.2 54.5646 100 25 -1.08 -0.4 W s 51.25883668981482 89.61245613425926 "" A 0 0
# plot_cross_section -159.6656 56 -159.6656 53.3 100 25 1.08 1.5 w s 51.25883668981482 89.61245613425926 "b) Seismicity between Simeonof and Sand Point" B 0 1
# plot_cross_section -160.2 54.5646 -159.2 54.5646 100 25 -1.08 -0.4 W S 89.61245613425926 999999999 "" A 1 0
# plot_cross_section -159.6656 56 -159.6656 53.3 100 25 1.08 1.5 w S 89.61245613425926 999999999 "c) Seismicity after Sand Point" B 1 1


gmt psconvert -A -P -Tf $PS
rm gmt.*
rm topo.grd
rm $PS