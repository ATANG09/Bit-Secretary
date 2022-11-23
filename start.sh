time=$(date "+%Y%m%d")
nohup python3 ./src/bit_secretary.py \
    --device 7 \
    --model_path ./src/quote_module/model/ \
    --max_output_length 256 \
    --num_beams 3 \
    --repetition_penalty 1.5 \
    > ./log/"${time}".log 2>&1