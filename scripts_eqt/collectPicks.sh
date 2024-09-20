workdir='/mnt/scratch/jieyaqi/alaska/final/eqt_2month'
output=$workdir/picks_raw.csv

for sta in `ls $workdir/detections`
do
    if [ ! -s $output ]
    then
        awk 'NR==1 {print $0}' $workdir/detections/$sta/X_prediction_results.csv > $output
    fi
    awk 'NR>1 {print $0}' $workdir/detections/$sta/X_prediction_results.csv >> $output
done