import json
import os
import hashlib
import sys

class AuthService:
    def __init__(self):
        # Determina o diretório base para salvar os arquivos
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.getcwd()
            
        self.USERS_FILE = os.path.join(self.base_path, "users.json")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.USERS_FILE):
            with open(self.USERS_FILE, 'w') as f:
                # Cria usuário padrão admin/admin
                default_users = {"admin": self._hash_password("admin")}
                json.dump(default_users, f)

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        try:
            with open(self.USERS_FILE, 'r') as f:
                users = json.load(f)
            
            if username in users and users[username] == self._hash_password(password):
                return True
            return False
        except:
            return False

    def register(self, username, password):
        try:
            with open(self.USERS_FILE, 'r') as f:
                users = json.load(f)
        except:
            users = {}
        
        if username in users:
            return False
            
        users[username] = self._hash_password(password)
        
        with open(self.USERS_FILE, 'w') as f:
            json.dump(users, f)
        return True
