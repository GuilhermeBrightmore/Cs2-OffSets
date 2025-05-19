import os
import shutil
import subprocess
import json
import re
import glob
import sys
from github import Github
from datetime import datetime
import time

# Configurações
OUTPUT_DIR = "A2X Generate Files"
CS2_DUMPER_PATH = "cs2-dumper.exe"
GITHUB_TOKEN = ""  # Token de acesso ao GitHub
REPO_NAME = "GuilhermeBrightmore/Cs2-OffSets"  # Formato: "usuario/nome_do_repo"
JSON_FILE_PATH = "offsets.json"  # Arquivo a ser enviado ao GitHub
COMMIT_MESSAGE = "Atualização automática de offsets via script Python"

# Função para converter o nome das variáveis em formato adequado para C++
def convert_name(name):
    return name.replace("::", "_").replace(" ", "_").replace("-", "_")

# Função para gerar o conteúdo do .hpp (sem valores definidos)
def generate_hpp(structs):
    hpp_content = ""

    for struct_name, variables in structs.items():
        hpp_content += f"inline struct {convert_name(struct_name)}Offsets {{\n"
        for var_name in variables:
            hpp_content += f"\tDWORD {convert_name(var_name)};\n"
        hpp_content += f"}} {convert_name(struct_name)};\n\n"

    return hpp_content

# Função para ler offsets e valores do arquivo .hpp
def parse_cpp_offsets(file_path):
    offsets = {}
    current_namespace = None

    # Expressão regular para capturar o início da namespace
    namespace_pattern = re.compile(r'namespace\s+(\w+)\s*\{')
    # Expressão regular para capturar o nome da variável e o valor associado
    offset_pattern = re.compile(r'constexpr\s+std::ptrdiff_t\s+(\w+)\s*=\s*(0x[0-9a-fA-F]+);')

    # Abrir e ler o arquivo .hpp
    with open(file_path, 'r', encoding='utf-8') as cpp_file:
        content = cpp_file.readlines()

        # Processar o conteúdo linha por linha
        for line in content:
            # Verificar se a linha contém a definição de uma namespace
            namespace_match = namespace_pattern.search(line)
            if namespace_match:
                current_namespace = namespace_match.group(1)
                if current_namespace not in offsets:
                    offsets[current_namespace] = {}

            # Verificar se a linha contém uma definição de variável com valor
            offset_match = offset_pattern.search(line)
            if offset_match and current_namespace:
                var_name = offset_match.group(1)
                var_value = offset_match.group(2)
                offsets[current_namespace][var_name] = var_value  # Adiciona o valor real da variável

    # Remove namespaces que não possuem variáveis
    offsets = {ns: vars for ns, vars in offsets.items() if vars}

    return offsets

# Função para salvar offsets em arquivo JSON
def save_offsets_to_json(offsets, output_file):
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(offsets, json_file, indent=4)

# Função para gerar código C++ para definir os offsets a partir do JSON no formato findOffsetByName
def generate_cpp_offset_code(json_file, output_cpp_file):
    print(f"[DEBUG] Gerando código C++ a partir do arquivo JSON: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    cpp_code = []

    # Percorre os namespaces no JSON
    for namespace, offsets in json_data.items():
        cpp_code.append(f"// Atribuições para {namespace}")
        cpp_code.append(f"// {namespace} Offsets")

        for var_name in offsets.keys():
            # Gera a linha no formato solicitado
            cpp_code.append(f'{namespace}.{convert_name(var_name)} = findOffsetByName(j, "{namespace}", "{var_name}");')

        cpp_code.append("")  # Adiciona uma linha em branco para separação

    # Grava o código gerado em um arquivo .cpp
    print(f"[DEBUG] Salvando o arquivo C++: {output_cpp_file}")
    with open(output_cpp_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(cpp_code))

# Função para processar todos os arquivos .hpp em um diretório
def process_all_cpp_files(directory):
    all_offsets = {}

    # Busca por todos os arquivos .hpp na pasta e subpastas
    cpp_files = glob.glob(os.path.join(directory, '**', '*.hpp'), recursive=True)

    for cpp_file in cpp_files:
        offsets = parse_cpp_offsets(cpp_file)

        # Combinar as offsets encontradas em todos os arquivos
        for namespace, namespace_offsets in offsets.items():
            if namespace not in all_offsets:
                all_offsets[namespace] = {}
            all_offsets[namespace].update(namespace_offsets)

    return all_offsets

# Função para fazer o commit do arquivo para o GitHub
def commit_to_github(file_path):
    try:
        # Inicializa o cliente GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Lê o conteúdo do arquivo
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Nome do arquivo no repositório (mantém apenas o nome base do arquivo)
        file_name = os.path.basename(file_path)
        
        # Verifica se o arquivo já existe no repositório
        try:
            contents = repo.get_contents(file_name)
            # Arquivo existe, faz update
            repo.update_file(
                contents.path, 
                COMMIT_MESSAGE, 
                content, 
                contents.sha
            )
            print(f"Arquivo {file_name} atualizado no GitHub com sucesso!")
        except:
            # Arquivo não existe, cria novo
            repo.create_file(
                file_name, 
                COMMIT_MESSAGE, 
                content
            )
            print(f"Arquivo {file_name} criado no GitHub com sucesso!")
        
        return True
    except Exception as e:
        print(f"Erro ao fazer commit para o GitHub: {str(e)}")
        return False

# Função principal que executa todo o processo
def main():
    try:
        # 1. Excluir e recriar o diretório de saída
        print(f"Recriando diretório: {OUTPUT_DIR}")
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)
        
        # 2. Executar o cs2-dumper.exe com os parâmetros necessários
        print("Executando cs2-dumper.exe...")
        # Construir o comando com -f e -o
        cmd = [CS2_DUMPER_PATH, "-f", "hpp", "-o", OUTPUT_DIR]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Verificar se a execução foi bem-sucedida
        if result.returncode != 0:
            print(f"Erro ao executar cs2-dumper: {result.stderr}")
            return False
        
        print("cs2-dumper executado com sucesso!")
        
        # 3. Aguardar um momento para garantir que os arquivos foram gerados
        time.sleep(2)
        
        # 4. Gerar os arquivos usando o código existente
        print("Gerando arquivos .json, .hpp e .cpp...")
        # Processar todos os arquivos .hpp
        all_offsets = process_all_cpp_files(OUTPUT_DIR)

        # Gera o arquivo JSON
        output_json = os.path.join(os.getcwd(), JSON_FILE_PATH)
        save_offsets_to_json(all_offsets, output_json)

        # Gera o arquivo HPP
        output_hpp = os.path.join(os.getcwd(), 'offsets.hpp')
        with open(output_hpp, 'w', encoding='utf-8') as hpp_file:
            hpp_file.write(generate_hpp(all_offsets))

        # Gera o arquivo C++ para as atribuições a partir do JSON
        output_cpp = os.path.join(os.getcwd(), 'set_offsets.cpp')
        generate_cpp_offset_code(output_json, output_cpp)

        print(f"Arquivos gerados: {output_json}, {output_hpp}, {output_cpp}")
        
        # 5. Fazer o commit do arquivo JSON para o GitHub
        print("Enviando o arquivo JSON para o GitHub...")
        commit_result = commit_to_github(output_json)
        
        if commit_result:
            print("Processo completo executado com sucesso!")
        else:
            print("Processo completo executado, mas ocorreu um erro no commit para o GitHub.")
        
    except Exception as e:
        print(f"Erro durante a execução: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("Iniciando processo de atualização de offsets...")
    main()