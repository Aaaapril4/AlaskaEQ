from string import Template

def generate_yaml(template:dir, outf: str, num: int):
    with open(template, 'r') as f:
        tem = f.readlines()

    t = Template(';'.join(tem))
    new_text = t.substitute(num=num)
    with open(outf, 'w') as f:
        f.writelines(new_text.split(';'))
    return 

if __name__ == '__main__':
    for i in range(1, 7):
        generate_yaml('scripts_phasenet/alaska_tonga.yaml', '/mnt/home/jieyaqi/code/PhaseNet-TF/configs/experiment', 'alaska_tonga', i)