import os
import re
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple

# Configurações globais
CAMINHO_RAIZ = r"\\abraao\NDDigital\NDDigital\Produtos\APPConnector\Especificos"
ARQUIVO_BUSCA = "config.xml"
TAGS_DESEJADAS = ["WSCompImpl"]

# Configurar logging apenas para console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class XMLTagExtractor:
    def __init__(self, tags_desejadas: List[str]):
        self.tags_desejadas = tags_desejadas
        self.total_arquivos_processados = 0
        self.total_tags_encontradas = 0
        self.arquivos_com_erros = 0

    def process_directory(self, caminho_raiz: str, arquivo_busca: str) -> None:
        """Processa todos os arquivos no diretório e subdiretórios"""
        if not os.path.isdir(caminho_raiz):
            raise ValueError(f"Caminho raiz inválido: {caminho_raiz}")

        logging.info("=== INÍCIO DA EXTRAÇÃO DE TAGS ===\n")
        
        for dirpath, _, filenames in os.walk(caminho_raiz):
            for filename in filenames:
                if filename.lower() == arquivo_busca.lower():
                    self.total_arquivos_processados += 1
                    caminho_completo = os.path.join(dirpath, filename)
                    logging.info(f"Processando arquivo: {caminho_completo}")
                    
                    conteudo, encoding = self._tentar_abrir_arquivo(caminho_completo)
                    if not conteudo:
                        self.arquivos_com_erros += 1
                        logging.error(f"❌ Erro ao ler {caminho_completo}\n")
                        continue
                    
                    self._procurar_classnames(caminho_completo, conteudo)

        # Exibe estatísticas finais
        self._exibir_estatisticas()

    def _procurar_classnames(self, caminho_arquivo: str, conteudo: str) -> None:
        """Procura pelas tags desejadas dentro dos ClassNames"""
        try:
            root = ET.fromstring(conteudo)
            tags_encontradas = set()
            classnames_por_tag = {tag: set() for tag in self.tags_desejadas}
            
            # Procurar por todas as tags ClassName
            for classname_node in root.findall(".//ClassName"):
                if classname_node.text:
                    classname = classname_node.text.strip()
                    # Verificar se o ClassName contém alguma das tags desejadas
                    for tag in self.tags_desejadas:
                        if tag.lower() in classname.lower():
                            classnames_por_tag[tag].add(classname)
                            tags_encontradas.add(tag)
            
            logging.info(f"Resultados para {caminho_arquivo}:")
            
            # Exibir cada tag encontrada apenas uma vez
            for tag in self.tags_desejadas:
                if tag in tags_encontradas:
                    # Pega o primeiro ClassName encontrado para esta tag
                    primeiro_classname = next(iter(classnames_por_tag[tag]))
                    logging.info(f"  {tag} encontrado: {primeiro_classname}")
                    self.total_tags_encontradas += 1
            
            tags_nao_encontradas = set(self.tags_desejadas) - tags_encontradas
            if tags_nao_encontradas:
                logging.info(f"  Tags não encontradas: {', '.join(tags_nao_encontradas)}")
            
            logging.info("")  # Linha em branco para separar os arquivos
            
        except Exception as e:
            logging.error(f"Erro ao parsear XML em {caminho_arquivo}: {e}\n")

    def _tentar_abrir_arquivo(self, caminho_arquivo: str) -> Tuple[Optional[str], Optional[str]]:
        """Tenta abrir um arquivo com diferentes encodings"""
        # Primeiro tenta detectar o encoding pela declaração XML
        encoding = self._detectar_encoding(caminho_arquivo)
        
        # Ordem de tentativa de encodings
        encodings_para_testar = [encoding] if encoding else []
        encodings_para_testar.extend([
            "utf-8",
            "utf-8-sig",
            "latin1",
            "iso-8859-1",
            "cp1252",
            "utf-16",
            "utf-16-le",
            "utf-16-be"
        ])

        for enc in encodings_para_testar:
            try:
                with open(caminho_arquivo, 'rb') as f:
                    bom = f.read(4)
                    f.seek(0)
                    
                    if bom.startswith(b'\xef\xbb\xbf'):
                        enc = 'utf-8-sig'
                    elif bom.startswith(b'\xff\xfe'):
                        enc = 'utf-16'
                    elif bom.startswith(b'\xfe\xff'):
                        enc = 'utf-16-be'
                    
                    conteudo = f.read().decode(enc)
                    if self._verificar_xml_valido(conteudo):
                        return conteudo, enc
            except (UnicodeDecodeError, LookupError, IOError) as e:
                continue
                
        logging.warning(f"Não foi possível decodificar o arquivo {caminho_arquivo}")
        return None, None

    def _detectar_encoding(self, caminho_arquivo: str) -> Optional[str]:
        """Detecta o encoding pela declaração XML"""
        try:
            with open(caminho_arquivo, 'rb') as f:
                primeira_linha = f.readline().decode('ascii', errors='ignore')
                if match := re.search(r'encoding=[\'"](.*?)[\'"]', primeira_linha):
                    return match.group(1).lower()
        except Exception as e:
            logging.warning(f"Erro ao detectar encoding: {e}")
        return None

    def _verificar_xml_valido(self, conteudo: str) -> bool:
        """Verifica se o conteúdo é um XML válido"""
        try:
            ET.fromstring(conteudo)
            return True
        except ET.ParseError:
            return False

    def _exibir_estatisticas(self) -> None:
        """Exibe estatísticas finais do processamento"""
        logging.info("\n=== ESTATÍSTICAS ===")
        logging.info(f"Total de arquivos processados: {self.total_arquivos_processados}")
        logging.info(f"Total de tags encontradas: {self.total_tags_encontradas}")
        logging.info(f"Arquivos com erros: {self.arquivos_com_erros}")
        logging.info("Processamento concluído!")

def main():
    try:
        logging.info("Iniciando processamento...")
        
        extractor = XMLTagExtractor(tags_desejadas=TAGS_DESEJADAS)
        extractor.process_directory(CAMINHO_RAIZ, ARQUIVO_BUSCA)
        
        logging.info("Processamento concluído com sucesso!")
    except Exception as e:
        logging.error(f"Erro fatal durante o processamento: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()