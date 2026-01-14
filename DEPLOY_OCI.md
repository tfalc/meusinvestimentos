# Guia de Deploy na Oracle Cloud (Free Tier)

Este guia ajuda você a implantar a Calculadora FII em uma instância **Always Free** (Ampere A1) da Oracle Cloud.

## 1. Criar a Instância (VM)
1. Acesse o console da Oracle Cloud.
2. Vá em **Compute > Instances > Create Instance**.
3. **Image/Shape**:
   - Imagem: Ubuntu 22.04 (ou Oracle Linux 8).
   - Shape: **Ampere (VM.Standard.A1.Flex)**. Selecione 2 ou 4 OCPUs e 12GB+ de RAM (é gratuito até 4 OCPUs/24GB).
4. **Networking**:
   - Crie uma VCN e Subnet pública padrão.
   - **Importante**: Baixe a chave SSH (Private Key) para conectar depois.
5. Clique em **Create**.

## 2. Liberar a Porta 8501 (Firewall)
Por padrão, apenas a porta 22 (SSH) é aberta.
1. Na página da instância, clique na **Subnet** (em "Primary VNIC").
2. Clique na **Security List** padrão.
3. Adicione uma **Ingress Rule**:
   - Source: `0.0.0.0/0`
   - Protocol: TCP
   - Destination Port Range: `8501`
   - Description: Streamlit

## 3. Conectar via SSH
Use um terminal (PowerShell, Git Bash ou Terminal do Mac/Linux):
```bash
# Ajuste o caminho da chave e o IP
ssh -i "caminho/para/sua-chave.key" ubuntu@IP_DA_SUA_INSTANCIA
```
*(Se usar Oracle Linux, o usuário é `opc` em vez de `ubuntu`)*.

## 4. Instalar Docker na VM
Execute estes comandos na VM para instalar o Docker:
```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER
# Saia e entre novamente para aplicar o grupo docker
exit
```
Reconecte via SSH.

## 5. Transferir e Rodar a Aplicação

### Opção A: Clonar do Git (Recomendado se o repo for público ou tiver token)
```bash
git clone https://github.com/SEU_USUARIO/CalculadoraFII.git
cd CalculadoraFII
docker build -t calculadora-fii .
```

### Opção B: Copiar arquivos via SCP (Se o código estiver só local)
Do seu computador local:
```bash
scp -i "chave.key" -r z:\TIC\git\CalculadoraFII ubuntu@IP_DA_VM:~/app
```
Na VM:
```bash
cd app
docker build -t calculadora-fii .
```

## 6. Rodar o Container (Com Persistência)
Para garantir que os dados (`portfolio_*.json`) não sumam ao reiniciar o container, vamos criar um volume mapeado para a pasta da VM.

1. Crie uma pasta para os dados na VM:
```bash
mkdir -p ~/fii_data
```

2. Rode o container:
```bash
docker run -d \
  -p 8501:8501 \
  --name meu-app-fii \
  --restart unless-stopped \
  -v ~/fii_data:/app \
  calculadora-fii
```
*Nota: O volume `-v ~/fii_data:/app` mapeia a pasta local para a pasta do app. Cuidado: isso pode sobrescrever o código se a pasta local estiver vazia. O ideal é mapear apenas os arquivos JSON se possível, ou usar um diretório específico para dados no código.*

**Ajuste Recomendado para Persistência Segura:**
Como o app salva os JSONs na raiz (`/app`), o mapeamento acima é arriscado (pode ocultar o código).
Melhor abordagem rápida:
Mapeie apenas os arquivos de dados (se já existirem) ou altere o código para salvar em `/app/data`.
Por enquanto, para simplificar, apenas rode sem volume persistente para testar, ou faça backup manual dos JSONs:

```bash
docker run -d -p 8501:8501 --name meu-app-fii calculadora-fii
```

## 7. Acessar
Abra no navegador: `http://IP_DA_SUA_INSTANCIA:8501`
