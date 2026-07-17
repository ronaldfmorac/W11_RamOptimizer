# ==============================================================================
# 📦 SECCIÓN 1: IMPORTACIONES, CONFIGURACIÓN GLOBAL Y PRIVILEGIOS
# ==============================================================================
import os
import sys
import threading
import ctypes
import json
import subprocess
import winreg
import psutil
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA IA DE GOOGLE GEMINI ---
API_KEY = "PUT_YOUR_API_KEY_HERE" 
genai.configure(api_key=API_KEY)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def es_administrador():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

class W11RamOptimizer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("W11 RamOptimizer")
        self.geometry("1200x850") # Ampliado para dar espacio a la consola SysAdmin
        
        # --- MODELOS EN CASCADA (Disponibilidad Total) ---
        self.gemini_models = [
            "gemini-3.5-flash",
            "gemini-3.1-pro-preview",
            "gemini-3.1-flash-lite",
            "gemini-2.5-pro",
            "gemini-2.5-flash"
        ]

        # --- VARIABLES ESTADO RAM ---
        self.procesos_suspendidos = {}
        self.apps_excluidas = set()
        self.datos_escaneo_actual = []
        self.procesos_bloqueados = set()
        self.nombres_amigables = {}
        self.categorias_ia = {}
        self.auto_refresh_activo = ctk.BooleanVar(value=False)
        self.reglas_guardian = {}
        
        # --- VARIABLES ESTADO SYSADMIN (RM_RO) ---
        self.datos_bloatware = []
        self.datos_telemetria = []
        self.datos_tareas = []
        self.cache_ia = {}
        self.ia_en_progreso = False
        self.tip_window = None
        
        self.descripciones_pestañas = {
            "☀️ Procesos Activos": "Muestra todos los procesos y aplicaciones que se están ejecutando en tiempo real en tu ordenador y cuánta memoria RAM consumen.",
            "🌙 Guardián": "Monitorea en segundo plano el sistema para suspender procesos que consumen demasiada energía o recursos de forma innecesaria.",
            "🚀 Inicio": "Gestiona los programas que se arrancan automáticamente al encender Windows. Desactivar los innecesarios acelera el inicio del PC.",
            "⚙️ Servicios": "Permite ver y controlar los servicios de fondo del sistema operativo Windows.",
            "📦 Software Basura": "Software Basura. Son aquellas aplicaciones preinstaladas de fábrica en Windows (juegos innecesarios, herramientas del fabricante) que ralentizan el PC y se pueden eliminar de forma segura.",
            "📡 Telemetría": "Configuración para deshabilitar el rastreo de datos de diagnóstico que Windows envía automáticamente a Microsoft.",
            "📅 Tareas": "Administrador de tareas programadas del sistema operativo."
        }

        self.lista_blanca = {
            'system idle process', 'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 
            'services.exe', 'lsass.exe', 'svchost.exe', 'fontdrvhost.exe', 'dwm.exe', 
            'spoolsv.exe', 'explorer.exe', 'taskmgr.exe', 'searchui.exe', 'winlogon.exe', 
            'sihost.exe', 'taskhostw.exe', 'conhost.exe', 'cmd.exe', 'powershell.exe',
            'python.exe', 'pythonw.exe', 'memcompression', 'bdservicehost.exe', 
            'msmpeng.exe', 'antimalware service executable', 'securityhealthservice.exe'
        }

        # --- ORDEN DE INICIALIZACIÓN ESTRICTO ---
        self.crear_interfaz()
        self.configurar_estilo_tabla()
        self.cargar_configuracion()
        self.verificar_guardian()
        self.actualizar_estado_ram()
        self.iniciar_escaneo()
        self.refrescar_todo_el_sistema()
        self.cargar_cache_ia_disco()
        self._renderizar_tablas_locales() 

# ==============================================================================
# 🎨 SECCIÓN 2: DISEÑO DE INTERFAZ UNIFICADA
# ==============================================================================
    def crear_interfaz(self):
        # Header Principal
        frame_header = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame_header.pack(fill="x", padx=20, pady=(15, 0))
        
        ctk.CTkLabel(frame_header, text="W11 RamOptimizer Core", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        
        # --- BOTÓN DE AYUDA GLOBAL (Se empaqueta primero a la derecha) ---
        btn_ayuda_global = ctk.CTkButton(frame_header, text="❓", width=30, height=30,
                                         fg_color="#1f6aa5", hover_color="#144870", text_color="white",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         command=self.mostrar_ayuda_pestaña_actual)
        btn_ayuda_global.pack(side="right", padx=(10, 0))
        
        self.lbl_ram_info = ctk.CTkLabel(frame_header, text="Calculando RAM...", font=ctk.CTkFont(size=12))
        self.lbl_ram_info.pack(side="right", padx=(10, 0))
        self.barra_ram = ctk.CTkProgressBar(frame_header, width=200)
        self.barra_ram.pack(side="right")
        self.barra_ram.set(0)

        if not es_administrador():
            ctk.CTkLabel(self, text="⚠️ Privilegios Limitados: Ejecuta como Administrador para Purga y Bloqueo", text_color="#ff5555").pack(pady=2)

        # TabView Central con 7 Pestañas Unificadas
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Pestañas Core (RAM)
        self.tabview.add("☀️ Procesos Activos")
        self.tabview.add("🌙 Guardián")
        self.tabview.add("🚀 Inicio")
        self.tabview.add("⚙️ Servicios")
        self.tabview.add("📦 Software Basura")
        self.tabview.add("📡 Telemetría")
        self.tabview.add("📅 Tareas")
        
       # al cambiar de pestaña haciendo clic
        self.tabview.configure(command=self.al_cambiar_pestaña)
        
        # Inicialización de sub-interfaces en cascada
        self.configurar_tab_activas()
        self.configurar_tab_suspendidas()  # Gestiona el contenedor interno de "🌙 Guardián"
        self.configurar_tab_inicio()
        self.configurar_tab_servicios()
        self.configurar_tab_bloatware()
        self.configurar_tab_telemetria()
        self.configurar_tab_tareas()

        # Consola SysAdmin Global
        frame_consola = ctk.CTkFrame(self, height=100)
        frame_consola.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(frame_consola, text="Terminal SysAdmin (Acciones del Sistema Real):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=2)
        
        self.txt_consola = ctk.CTkTextbox(frame_consola, height=70, fg_color="#1a1a1a", text_color="#4dff88", font=("Consolas", 11))
        self.txt_consola.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.txt_consola.configure(state="disabled")
        
    def configurar_estilo_tabla(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=25, fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat")
        
        # Mapeo y asignación segura de tags de clasificación de IA para todos los módulos
        tablas_sistema = [
            "tabla_activas", 
            "tabla_suspendidas", 
            "tabla_inicio", 
            "tabla_servicios", 
            "tabla_bloatware", 
            "tabla_telemetria", 
            "tabla_tareas"
        ]
        
        for attr_name in tablas_sistema:
            tabla = getattr(self, attr_name, None)
            if tabla is not None:
                tabla.tag_configure("critico", foreground="#ff4d4d")
                tabla.tag_configure("seguro", foreground="#4dff88")
                tabla.tag_configure("sospechoso", foreground="#ffb84d")
                tabla.tag_configure("bloqueado", foreground="#a6a6a6")
                tabla.bind("<Motion>", self.controlar_tooltip_dinamico)
                tabla.bind("<Leave>", lambda e: self.ocultar_tooltip())

# ==============================================================================
# 🧩 SECCIÓN 3: CONFIGURACIÓN DE PESTAÑAS (Módulos de UI)
# ==============================================================================
    # --- PESTAÑAS RAM OPTIMIZER BASE ---
    def configurar_tab_activas(self):
        tab = self.tabview.tab("☀️ Procesos Activos")
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill="x", pady=5)
        
        ctk.CTkButton(frame_top, text="🧠 Analizar RAM con IA", fg_color="#673ab7", hover_color="#512da8", command=self.analizar_con_ia).pack(side="left", padx=5)
        
        self.combo_perfiles = ctk.CTkOptionMenu(frame_top, values=["Modo Normal", "Modo Gamer (Suspender)", "Modo Turbo (Cierre)"], width=180)
        self.combo_perfiles.pack(side="left", padx=5)
        self.combo_perfiles.set("Modo Normal")
        
        ctk.CTkButton(frame_top, text="⚡ Aplicar Perfil", fg_color="#ff9900", hover_color="#e68a00", text_color="#000", command=self.ejecutar_perfil_ia).pack(side="left", padx=5)
        
        # --- AQUÍ LA ADAPTACIÓN PERFECTA PARA TU INTERFAZ ---
        # Primero empaquetamos el botón de Refrescar a la derecha
        ctk.CTkButton(frame_top, text="🔄 Refrescar", width=90, command=self.iniciar_escaneo).pack(side="right", padx=5)
        

        # Contenedor de Tabla y Scrollbar para evitar congelamiento visual
        frame_tabla = ctk.CTkFrame(tab, fg_color="transparent")
        frame_tabla.pack(fill="both", expand=True, pady=5)

        self.tabla_activas = ttk.Treeview(frame_tabla, columns=("Candado", "App", "Ejecutable", "PIDs", "RAM", "Estado IA"), show="headings")
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_activas.yview)
        self.tabla_activas.configure(yscrollcommand=scrollbar.set)
        
        for col, texto in zip(self.tabla_activas["columns"], ["🔒", "App", "Ejecutable", "PIDs", "RAM", "Estado IA"]):
            self.tabla_activas.heading(col, text=texto)
        
        self.tabla_activas.column("Candado", width=50, anchor="center")
        self.tabla_activas.column("App", width=200, anchor="w")
        self.tabla_activas.column("Ejecutable", width=150, anchor="w")
        self.tabla_activas.column("PIDs", width=100, anchor="center")
        self.tabla_activas.column("RAM", width=100, anchor="e")
        self.tabla_activas.column("Estado IA", width=250, anchor="w")
        
        self.tabla_activas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Vinculación de doble clic para alternar exclusión (Lista Blanca / Candado)
        self.tabla_activas.bind("<Double-1>", self.alternar_exclusion_candado)

        frame_acciones = ctk.CTkFrame(tab, fg_color="transparent")
        frame_acciones.pack(fill="x", pady=5)
        
        ctk.CTkButton(frame_acciones, text="⏸️ Suspender", fg_color="#d48a00", command=self.suspender_app).pack(side="left", padx=5)
        ctk.CTkButton(frame_acciones, text="💀 Forzar Cierre", fg_color="#c93434", command=self.matar_app).pack(side="left", padx=5)
        ctk.CTkButton(frame_acciones, text="💡 Explicar con IA", fg_color="#4a148c", command=lambda: self.lanzar_explicador("proceso")).pack(side="left", padx=15)
        
    def configurar_tab_suspendidas(self):
        tab = self.tabview.tab("🌙 Guardián")
        
        frame_tabla = ctk.CTkFrame(tab, fg_color="transparent")
        frame_tabla.pack(fill="both", expand=True, pady=5)

        self.tabla_suspendidas = ttk.Treeview(frame_tabla, columns=("App", "Estado", "Regla"), show="headings")
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_suspendidas.yview)
        self.tabla_suspendidas.configure(yscrollcommand=scrollbar.set)
        
        for col in self.tabla_suspendidas["columns"]: 
            self.tabla_suspendidas.heading(col, text=col)
            self.tabla_suspendidas.column(col, anchor="w" if col != "Estado" else "center")
            
        self.tabla_suspendidas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame_btn = ctk.CTkFrame(tab, fg_color="transparent")
        frame_btn.pack(pady=5)
        ctk.CTkButton(frame_btn, text="▶️ Reanudar App", fg_color="#28a745", command=self.reanudar_app).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="🔄 Alternar Regla", fg_color="#007acc", command=self.alternar_regla_guardian).pack(side="left", padx=5)

    def configurar_tab_inicio(self):
        tab = self.tabview.tab("🚀 Inicio")
        
        frame_tabla = ctk.CTkFrame(tab, fg_color="transparent")
        frame_tabla.pack(fill="both", expand=True, pady=5)

        self.tabla_inicio = ttk.Treeview(frame_tabla, columns=("Nombre", "Comando", "Ubicación"), show="headings")
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_inicio.yview)
        self.tabla_inicio.configure(yscrollcommand=scrollbar.set)
        
        for col in self.tabla_inicio["columns"]: 
            self.tabla_inicio.heading(col, text=col)
            self.tabla_inicio.column(col, anchor="w")
            
        self.tabla_inicio.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        ctk.CTkButton(tab, text="❌ Deshabilitar del Inicio", fg_color="#c93434", command=self.deshabilitar_programa_inicio).pack(pady=5)
        self.after(500, self.leer_programas_inicio)

    def configurar_tab_servicios(self):
        tab = self.tabview.tab("⚙️ Servicios")
        
        frame_tabla = ctk.CTkFrame(tab, fg_color="transparent")
        frame_tabla.pack(fill="both", expand=True, pady=5)

        self.tabla_servicios = ttk.Treeview(frame_tabla, columns=("Interno", "Visible", "Estado", "Inicio"), show="headings")
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_servicios.yview)
        self.tabla_servicios.configure(yscrollcommand=scrollbar.set)
        
        for col in self.tabla_servicios["columns"]: 
            self.tabla_servicios.heading(col, text=col)
            self.tabla_servicios.column(col, anchor="w" if col != "Estado" else "center")
            
        self.tabla_servicios.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame_btn = ctk.CTkFrame(tab, fg_color="transparent")
        frame_btn.pack(pady=5)
        ctk.CTkButton(frame_btn, text="🛑 Detener/Deshabilitar", fg_color="#c93434", command=self.deshabilitar_servicio_windows).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="💡 Explicar con IA", fg_color="#4a148c", command=lambda: self.lanzar_explicador("servicio")).pack(side="left", padx=5)
        self.after(500, self.listar_servicios_windows)

    # --- PESTAÑAS SYSADMIN (RM_RO INTEGRADO) ---
    def configurar_tab_bloatware(self):
        tab = self.tabview.tab("📦 Software Basura")
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill="x", pady=5)
        
        ctk.CTkButton(frame_top, text="🧠 Diagnóstico Profundo IA", fg_color="#673ab7", command=self.analizar_sistema_con_ia).pack(side="left", padx=5)
        
        # Selector Dinámico de Modelos Gemini integrado en la barra de control SysAdmin
        ctk.CTkLabel(frame_top, text="Modelo IA:").pack(side="right", padx=2)
        self.combo_modelos_ia = ctk.CTkOptionMenu(frame_top, values=self.gemini_models, width=180)
        self.combo_modelos_ia.pack(side="right", padx=5)
        self.combo_modelos_ia.set(self.gemini_models[0])
        
        frame_tabla = ctk.CTkFrame(tab, fg_color="transparent")
        frame_tabla.pack(fill="both", expand=True, pady=5)

        self.tabla_bloatware = ttk.Treeview(frame_tabla, columns=("ID", "Nombre", "Editor", "Estado IA"), show="headings")
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_bloatware.yview)
        self.tabla_bloatware.configure(yscrollcommand=scrollbar.set)
        
        for col in self.tabla_bloatware["columns"]: 
            self.tabla_bloatware.heading(col, text=col)
            self.tabla_bloatware.column(col, anchor="w")
            
        self.tabla_bloatware.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame_btn = ctk.CTkFrame(tab, fg_color="transparent")
        frame_btn.pack(pady=5)
        ctk.CTkButton(frame_btn, text="🗑️ Desinstalar (Winget)", fg_color="#c93434", command=self.ejecutar_desinstalacion_bloatware).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="💡 Explicar con IA", fg_color="#4a148c", command=lambda: self.lanzar_explicador("Software Basura")).pack(side="left", padx=5)

    def configurar_tab_telemetria(self):
        tab = self.tabview.tab("📡 Telemetría")
        
        frame_tabla = ctk.CTkFrame(tab, fg_color="transparent")
        frame_tabla.pack(fill="both", expand=True, pady=5)

        self.tabla_telemetria = ttk.Treeview(frame_tabla, columns=("Componente", "Tipo", "Estado", "Estado IA"), show="headings")
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_telemetria.yview)
        self.tabla_telemetria.configure(yscrollcommand=scrollbar.set)
        
        for col in self.tabla_telemetria["columns"]: 
            self.tabla_telemetria.heading(col, text=col)
            self.tabla_telemetria.column(col, anchor="w" if col != "Estado" else "center")
            
        self.tabla_telemetria.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame_btn = ctk.CTkFrame(tab, fg_color="transparent")
        frame_btn.pack(pady=5)
        ctk.CTkButton(frame_btn, text="🛑 Capar Elemento", fg_color="#d48a00", command=self.ejecutar_bloqueo_telemetria).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="💡 Explicar con IA", fg_color="#4a148c", command=lambda: self.lanzar_explicador("telemetria")).pack(side="left", padx=5)

    def configurar_tab_tareas(self):
        tab = self.tabview.tab("📅 Tareas")
        
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill="x", pady=5)
        
        ctk.CTkButton(frame_top, text="🧠 Analizar Tareas con IA", fg_color="#673ab7", hover_color="#512da8", command=self.analizar_tareas_con_ia).pack(side="left", padx=5)
        
        frame_tabla = ctk.CTkFrame(tab, fg_color="transparent")
        frame_tabla.pack(fill="both", expand=True, pady=5)

        self.tabla_tareas = ttk.Treeview(frame_tabla, columns=("Ruta", "Nombre", "Estado", "Estado IA"), show="headings")
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_tareas.yview)
        self.tabla_tareas.configure(yscrollcommand=scrollbar.set)
        
        for col in self.tabla_tareas["columns"]: 
            self.tabla_tareas.heading(col, text=col)
            self.tabla_tareas.column(col, anchor="w" if col != "Estado" else "center")
            
        self.tabla_tareas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame_btn = ctk.CTkFrame(tab, fg_color="transparent")
        frame_btn.pack(pady=5)
        ctk.CTkButton(frame_btn, text="📅 Deshabilitar Tarea", fg_color="#007acc", command=self.ejecutar_desactivacion_tarea).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="💡 Explicar con IA", fg_color="#4a148c", command=lambda: self.lanzar_explicador("tarea")).pack(side="left", padx=5)

# ==============================================================================
# ℹ️ SISTEMA DE TOOLTIPS DINÁMICOS EXPLICATIVOS
# ==============================================================================
    def controlar_tooltip_dinamico(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        # Si no estamos sobre un elemento válido, ocultar el tooltip
        if not item:
            self.ocultar_tooltip()
            return
            
        valores = tree.item(item, "values")
        if not valores:
            return

        texto = ""
        
        # Textos explicativos base de Inteligencia Artificial
        textos_ia = {
            "Critico": "🚨 RECOMENDACIÓN URGENTE:\nEste elemento consume muchos recursos o es Software Basura/Telemetría nociva.\nLa IA aconseja mitigarlo para optimizar CPU y RAM.",
            "Sospechoso": "⚠️ RECOMENDACIÓN PRESCINDIBLE:\nEs un proceso secundario o de terceros no esencial.\nEs seguro deshabilitarlo o suspenderlo para exprimir rendimiento.",
            "Seguro": "✅ RECOMENDACIÓN MANTENER:\nComponente legítimo y crítico para la estabilidad de Windows o tus aplicaciones.\nLa IA aconseja no tocarlo.",
            "Pendiente": "⏳ DIAGNÓSTICO EN ESPERA:\nEste elemento no ha sido evaluado aún por Gemini.\nEjecuta el análisis IA para procesarlo."
        }

        # 1. Lógica para Pestaña "☀️ Activas" (El estado IA está en la columna #6)
        if tree == getattr(self, "tabla_activas", None) and column == "#6":
            if len(valores) >= 6:
                texto = textos_ia.get(valores[5], "")

        # 2. Lógica para Pestaña "🌙 Guardián" (La regla está en la columna #3)
        elif tree == getattr(self, "tabla_suspendidas", None) and column == "#3":
            if len(valores) >= 3:
                regla = valores[2]
                if regla == "Auto-Suspender":
                    texto = "🛡️ AUTO-SUSPENDER:\nEl Guardián interceptará automáticamente esta app en segundo plano\ny congelará sus hilos para liberar CPU inmediatamente."
                elif regla == "Ninguna":
                    texto = "ℹ️ NINGUNA:\nEsta app está suspendida manualmente.\nEl Guardián no actuará de forma automática si la app se reinicia."

        # 3. Lógica para Pestañas SysAdmin (El estado IA está en la columna #4)
        elif tree in [getattr(self, "tabla_bloatware", None), getattr(self, "tabla_telemetria", None), getattr(self, "tabla_tareas", None)] and column == "#4":
            if len(valores) >= 4:
                texto = textos_ia.get(valores[3], "")

        # Mostrar u ocultar dependiendo de si obtuvimos texto
        if texto:
            self.mostrar_tooltip(event.x_root + 15, event.y_root + 15, texto)
        else:
            self.ocultar_tooltip()
            
    def controlar_tooltip_pestañas(self, event):
        """Actualiza el texto de la barra de estado según la pestaña."""
        seg_button = self.tabview._segmented_button
        pestaña_detectada = None
        
        # CustomTkinter tiene un método nativo para saber qué botón está bajo el cursor en X
        # sin necesidad de calcular anchos manualmente
        mouse_x = event.x
        
        for name, button in seg_button._buttons_dict.items():
            bx = button.winfo_x()
            bw = button.winfo_width()
            if bx <= mouse_x <= (bx + bw):
                pestaña_detectada = name
                break
                
        if pestaña_detectada and pestaña_detectada in self.descripciones_pestañas:
            texto_ayuda = self.descripciones_pestañas[pestaña_detectada].replace("\n", " ")
            self.barra_estado.configure(text=f"💡 {pestaña_detectada}: {texto_ayuda}")
        else:
            self.barra_estado.configure(text="Listo")

    def mostrar_tooltip(self, x, y, texto):
        if self.tip_window:
            self.tip_label.configure(text=texto)
            self.tip_window.wm_geometry(f"+{x}+{y}")
            return
            
        self.tip_window = tk.Toplevel(self)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        self.tip_window.attributes("-topmost", True)
        
        # Diseño visual del tooltip
        frame = tk.Frame(self.tip_window, bg="#1e1e1e", padx=10, pady=8, highlightbackground="#565b5e", highlightthickness=1)
        frame.pack()
        
        self.tip_label = tk.Label(frame, text=texto, bg="#1e1e1e", fg="#ffffff", justify="left", font=("Segoe UI", 10))
        self.tip_label.pack()

    def ocultar_tooltip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ==============================================================================
# 🧠 SECCIÓN 4: MOTOR DE EXPLICACIÓN IA GLOBAL (Unificado y Resiliente)
# ==============================================================================
    def obtener_telemetria_proceso(self, ejecutable):
        """Busca un proceso activo por su nombre ejecutable y extrae su ruta y consumo real."""
        datos = {"ruta": "Desconocida o Protegida", "ram": "0"}
        for proc in psutil.process_iter(['name', 'exe', 'memory_info']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == ejecutable.lower():
                    if proc.info['exe']:
                        datos["ruta"] = proc.info['exe']
                    if proc.info['memory_info']:
                        datos["ram"] = f"{proc.info['memory_info'].rss / (1024 * 1024):.1f}"
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return datos

    def lanzar_explicador(self, tipo):
        """Recopila datos de forma segura según la pestaña activa y lanza la ventana de análisis IA."""
        identificador = ""
        extra_info = {}
        
        try:
            if tipo == "proceso":
                sel = self.tabla_activas.selection()
                if not sel: 
                    return messagebox.showwarning("Aviso", "Por favor, selecciona un proceso activo de la lista.")
                valores = self.tabla_activas.item(sel[0], "values")
                if len(valores) > 2:
                    identificador = valores[2]  # Nombre del ejecutable
                    extra_info = self.obtener_telemetria_proceso(identificador)
                    if extra_info["ram"] == "0" and len(valores) > 4:
                        extra_info["ram"] = valores[4].replace(" MB", "")

            elif tipo == "servicio":
                sel = self.tabla_servicios.selection()
                if not sel: 
                    return messagebox.showwarning("Aviso", "Por favor, selecciona un servicio de Windows.")
                valores = self.tabla_servicios.item(sel[0], "values")
                if len(valores) > 1:
                    identificador = valores[0]  # Nombre interno del servicio
                    extra_info = {"display_name": valores[1], "estado": valores[2] if len(valores) > 2 else "Desconocido"}

            elif tipo == "Software Basura":
                sel = self.tabla_bloatware.selection()
                if not sel: 
                    return messagebox.showwarning("Aviso", "Por favor, selecciona una aplicación de la lista.")
                valores = self.tabla_bloatware.item(sel[0], "values")
                if len(valores) > 2:
                    identificador = valores[1]  # Nombre de la App
                    extra_info = {"id_package": valores[0], "publisher": valores[2]}

            elif tipo == "telemetria":
                sel = self.tabla_telemetria.selection()
                if not sel: 
                    return messagebox.showwarning("Aviso", "Por favor, selecciona un componente de telemetría.")
                valores = self.tabla_telemetria.item(sel[0], "values")
                if len(valores) > 0:
                    identificador = valores[0]  # Clave de registro o servicio
                    extra_info = {"tipo": valores[1] if len(valores) > 1 else "Componente"}

            elif tipo == "tarea":
                sel = self.tabla_tareas.selection()
                if not sel: 
                    return messagebox.showwarning("Aviso", "Por favor, selecciona una tarea programada.")
                valores = self.tabla_tareas.item(sel[0], "values")
                if len(valores) > 1:
                    identificador = valores[1]  # Nombre de la tarea
                    extra_info = {"ruta": valores[0], "estado": valores[2] if len(valores) > 2 else "Desconocido"}

            if identificador:
                self.abrir_ventana_explicadora(identificador, tipo, extra_info)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron recopilar los metadatos para el análisis: {str(e)}")

    def mostrar_ayuda_pestaña_actual(self):
        """Detecta la pestaña activa actual y despliega un cuadro de diálogo con su descripción."""
        from tkinter import messagebox
        
        # CustomTkinter nos da el nombre exacto de la pestaña que el usuario está viendo
        pestaña_actual = self.tabview.get()
        
        # Buscamos la descripción en tu diccionario self.descripciones_pestañas
        info = self.descripciones_pestañas.get(pestaña_actual, "Sin descripción disponible para esta sección.")
        
        # Mostramos el cuadro de diálogo
        messagebox.showinfo(
            title=f"Ayuda del Sistema: {pestaña_actual}",
            message=info
        )

    def al_cambiar_pestaña(self):
        """Método seguro por si necesitas ejecutar acciones al cambiar de pestaña."""
        pass

    def abrir_ventana_explicadora(self, identificador, tipo, extra_info):
        """Crea una interfaz asíncrona dedicada para mostrar la auditoría e investigación del elemento."""
        ventana_ia = ctk.CTkToplevel(self)
        ventana_ia.title(f"Auditoría Inteligente - {identificador}")
        ventana_ia.geometry("650x500")
        ventana_ia.minsize(500, 400)
        ventana_ia.attributes("-topmost", True)
        
        # Centrar ventana respecto a la aplicación principal
        ventana_ia.lift()
        ventana_ia.focus_force()

        ctk.CTkLabel(
            ventana_ia, 
            text=f"Análisis Avanzado de Sistema", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 2))
        
        ctk.CTkLabel(
            ventana_ia, 
            text=f"Target: {identificador}", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#a6a6a6"
        ).pack(pady=(0, 10))

        caja_explicacion = ctk.CTkTextbox(ventana_ia, font=("Segoe UI", 12), wrap="word")
        caja_explicacion.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        caja_explicacion.insert("0.0", "🧠 Conectando con los modelos neuronales de Gemini...\nEvaluando integridad, dependencias y árbol de procesos del sistema. Por favor, espera...")
        caja_explicacion.configure(state="disabled")

        def consultar_explicador():
            try:
                # Construcción semántica y estricta del Prompt de Inyección de Contexto
                prompt = (
                    f"Actúa como un Ingeniero de Software Experto en Windows Internals y Ciberseguridad. "
                    f"Analiza el siguiente componente del sistema: '{identificador}'.\n\n"
                    f"Contexto operativo detectado en la máquina del usuario:\n"
                )
                
                if tipo == "proceso":
                    prompt += (
                        f"- Tipo: Proceso Activo en Memoria RAM\n"
                        f"- Ruta del ejecutable: {extra_info.get('ruta')}\n"
                        f"- Consumo de RAM registrado: {extra_info.get('ram')} MB\n\n"
                        f"Por favor, responde estructuradamente en español:\n"
                        f"1) ¿Qué es exactamente este ejecutable y qué función cumple?\n"
                        f"2) ¿Es un proceso nativo crítico de Windows, software legítimo de terceros o sospechoso?\n"
                        f"3) ¿Es seguro forzar su cierre (Kill) o suspenderlo? ¿Qué impacto tendrá en el sistema operativo?"
                    )
                elif tipo == "servicio":
                    prompt += (
                        f"- Tipo: Servicio de Windows NT\n"
                        f"- Nombre Visible: {extra_info.get('display_name')}\n"
                        f"- Estado de ejecución: {extra_info.get('estado')}\n\n"
                        f"Por favor, responde estructuradamente en español:\n"
                        f"1) ¿Cuál es el propósito real de este servicio?\n"
                        f"2) ¿Qué sucede si se detiene o se deshabilita de raíz en el registro?\n"
                        f"3) ¿Es recomendado optimizarlo para recuperar rendimiento o memoria?"
                    )
                elif tipo == "Software Basura":
                    prompt += (
                        f"- Tipo: Aplicación Instalada en el Sistema\n"
                        f"- Identificador de paquete: {extra_info.get('id_package')}\n"
                        f"- Desarrollador/Editor: {extra_info.get('publisher')}\n\n"
                        f"Por favor, responde estructuradamente en español:\n"
                        f"1) ¿Para qué sirve esta aplicación y cómo llegó al sistema (Software Basura OEM, telemetría o app de usuario)?\n"
                        f"2) ¿Su eliminación mediante el gestor Winget causa inestabilidad en Windows o pérdida de funciones?\n"
                        f"3) ¿Recomiendas su desinstalación inmediata para limpiar almacenamiento y subprocesos de fondo?"
                    )
                elif tipo == "telemetria":
                    prompt += (
                        f"- Tipo: Componente / Nodo de Telemetría o Recolección de Datos\n"
                        f"- Naturaleza del elemento: {extra_info.get('tipo')}\n\n"
                        f"Por favor, responde estructuradamente en español:\n"
                        f"1) ¿Qué datos recolecta o transmite este elemento específico hacia los servidores?\n"
                        f"2) ¿Mitiga el rendimiento de la CPU, red o disco al ejecutarse en segundo plano?\n"
                        f"3) ¿Es 100% seguro capar/bloquear este elemento y qué directiva o servicio se ve afectado?"
                    )
                elif tipo == "tarea":
                    prompt += (
                        f"- Tipo: Tarea Programada (Task Scheduler Element)\n"
                        f"- Ubicación en el árbol de tareas: {extra_info.get('ruta')}\n"
                        f"- Estado actual: {extra_info.get('estado')}\n\n"
                        f"Por favor, responde estructuradamente en español:\n"
                        f"1) ¿Qué disparador activa esta tarea y qué script o ejecutable corre internamente?\n"
                        f"2) ¿Es una tarea necesaria para actualizaciones automáticas, mantenimiento crítico o es prescindible?\n"
                        f"3) ¿Es seguro y recomendado deshabilitarla para evitar picos repentinos de uso de recursos?"
                    )

                # Ejecución de la consulta con el mecanismo de cascada de resiliencia
                respuesta, modelo_utilizado = self.ejecutar_consulta_gemini_cascada(prompt)
                texto_final = f"🤖 [Analizado de forma exitosa con: {modelo_utilizado}]\n\n{respuesta}"
                
                self.after(0, lambda: actualizar_texto_ventana(texto_final))
            except Exception as e:
                self.after(0, lambda: actualizar_texto_ventana(f"❌ Error crítico en la consulta de IA:\n\n{str(e)}\n\nPor favor, verifica tu conexión a internet o la validez de la API Key configurada."))

        def actualizar_texto_ventana(texto):
            if ventana_ia.winfo_exists():
                caja_explicacion.configure(state="normal")
                caja_explicacion.delete("1.0", tk.END)
                caja_explicacion.insert("1.0", texto)
                caja_explicacion.configure(state="disabled")

        # Desplegar la consulta en un hilo secundario para evitar bloqueos del bucle principal de tkinter
        threading.Thread(target=consultar_explicador, daemon=True).start()

    def ejecutar_consulta_gemini_cascada(self, prompt):
        """Mecanismo de tolerancia a fallos. Intenta resolver la consulta usando el modelo seleccionado

        por el usuario en la interfaz, y si falla, recorre la cascada de modelos disponibles."""
        ultimo_error = None
        
        # Determinar el orden de evaluación de modelos dando prioridad a la UI
        modelos_ordenados = list(self.gemini_models)
        if hasattr(self, 'combo_modelos_ia'):
            modelo_preferido = self.combo_modelos_ia.get()
            if modelo_preferido in modelos_ordenados:
                modelos_ordenados.remove(modelo_preferido)
                modelos_ordenados.insert(0, modelo_preferido)
        
        for modelo_nombre in modelos_ordenados:
            try:
                model = genai.GenerativeModel(modelo_nombre)
                respuesta = model.generate_content(prompt)
                if respuesta and respuesta.text:
                    return respuesta.text, modelo_nombre
                else:
                    raise ValueError("El modelo retornó un cuerpo de respuesta vacío o bloqueado por seguridad.")
            except Exception as e:
                ultimo_error = e
                print(f"[MÓDULO IA] Caída/Timeout en modelo '{modelo_nombre}'. Saltando al siguiente... Motivo: {e}")
                continue
                
        raise Exception(f"Fallo total en cascada de Inteligencia Artificial. Último error registrado: {ultimo_error}")

# ==============================================================================
# 💾 SECCIÓN 5: PERSISTENCIA UNIFICADA (JSON)
# ==============================================================================
    def _obtener_ruta_config(self):
        """Calcula de forma segura la ruta del archivo de configuración, resolviendo compatibilidad

        con entornos compilados de empaquetado (PyInstaller/cx_Freeze)."""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "config_optimizador.json")

    def cargar_configuracion(self):
        """Carga de manera centralizada toda la configuración global del optimizador, la exclusión de

        procesos y los metadatos del módulo SysAdmin optimizando los ciclos de E/S de disco."""
        ruta = self._obtener_ruta_config()
        if not os.path.exists(ruta):
            return
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            
            # Deserialización segura de colecciones de tipo Set
            self.procesos_bloqueados = set(datos.get("procesos_bloqueados", []))
            self.apps_excluidas = set(datos.get("apps_excluidas", []))  # Recuperación de la exclusión por candado de la interfaz
            
            # Deserialización de estructuras de mapeo y diccionarios core
            self.nombres_amigables = datos.get("nombres_amigables", {})
            self.categorias_ia = datos.get("categorias_ia", {})
            self.reglas_guardian = datos.get("reglas_guardian", {})
            
            # Carga preventiva y anticipada de la caché SysAdmin para mitigar desincronizaciones
            if "cache_ia_profunda" in datos:
                self.cache_ia = datos.get("cache_ia_profunda", {})
                
        except Exception as e:
            error_msg = f"⚠️ Fallo al parsear la configuración JSON: {str(e)}"
            if hasattr(self, 'log_consola'):
                self.log_consola(error_msg)
            else:
                print(error_msg)

    def guardar_configuracion(self):
        """Serializa de manera segura y atómica el estado operativo actual de las variables de memoria

        y de las respuestas del modelo heurístico en el archivo de configuración local."""
        ruta = self._obtener_ruta_config()
        datos = {}
        
        # Lectura previa del estado del archivo en disco para prevenir la pérdida de llaves huérfanas
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            except Exception:
                datos = {}
        
        # Mezcla y actualización atómica de las estructuras mutables
        datos.update({
            "procesos_bloqueados": list(self.procesos_bloqueados),
            "apps_excluidas": list(self.apps_excluidas),  # Persistencia del estado del candado de protección
            "nombres_amigables": self.nombres_amigables,
            "categorias_ia": self.categorias_ia,
            "reglas_guardian": self.reglas_guardian,
            "cache_ia_profunda": self.cache_ia
        })
        
        try:
            # Implementación de guardado atómico mediante archivo temporal (.tmp) para blindar la data de apagados abruptos
            ruta_temporal = ruta + ".tmp"
            with open(ruta_temporal, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            
            if os.path.exists(ruta_temporal):
                if os.path.exists(ruta):
                    os.remove(ruta)
                os.rename(ruta_temporal, ruta)
                
        except Exception as e:
            error_msg = f"⚠️ Error de flujo crítico al escribir persistencia en disco: {str(e)}"
            if hasattr(self, 'log_consola'):
                self.log_consola(error_msg)
            else:
                print(error_msg)

    def cargar_cache_ia_disco(self):
        """Mantiene compatibilidad con el orden secuencial de inicialización, verificando e

        informando el estado de los componentes indexados de la caché profunda en la terminal."""
        ruta = self._obtener_ruta_config()
        if os.path.exists(ruta):
            try:
                # Verificación de respaldo si el flujo secuencial requiere lectura forzada
                if not self.cache_ia:
                    with open(ruta, "r", encoding="utf-8") as f:
                        datos = json.load(f)
                    self.cache_ia = datos.get("cache_ia_profunda", {})
                
                # Reporte formalizado de sincronización exitosa a la consola SysAdmin global
                if hasattr(self, 'log_consola'):
                    self.log_consola(f"📦 [Persistencia] Caché IA indexada y sincronizada correctamente ({len(self.cache_ia)} elementos cargados).")
            except Exception as e:
                if hasattr(self, 'log_consola'):
                    self.log_consola(f"⚠️ Error al sincronizar el buffer de la caché de IA: {str(e)}")

# ==============================================================================
# ⚙️ SECCIÓN 6: LÓGICA CORE (RAM, Escaneo, Funciones Auxiliares)
# ==============================================================================
    def log_consola(self, texto):
        """Escribe un log cronológico estructurado en la consola SysAdmin global."""
        if hasattr(self, 'txt_consola') and self.txt_consola.winfo_exists():
            self.txt_consola.configure(state="normal")
            self.txt_consola.insert(tk.END, f"[SYS] {texto}\n")
            self.txt_consola.see(tk.END)
            self.txt_consola.configure(state="disabled")

    def actualizar_estado_ram(self):
        """Monitorea el consumo global de memoria RAM física del sistema operativo en tiempo real."""
        try:
            mem = psutil.virtual_memory()
            self.barra_ram.set(mem.percent / 100)
            self.lbl_ram_info.configure(text=f"RAM: {mem.percent}% ({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)")
        except Exception:
            pass
        self.after(2000, self.actualizar_estado_ram)

    def iniciar_escaneo(self):
        """Lanza el hilo de escaneo asíncrono para no congelar el dibujado de la interfaz gráfica."""
        for item in self.tabla_activas.get_children():
            self.tabla_activas.delete(item)
        threading.Thread(target=self.procesar_escaneo, daemon=True).start()

    def procesar_escaneo(self):
        """Analiza, agrupa por ejecutable y calcula el consumo de memoria de todos los hilos del sistema."""
        apps_agrupadas = {}
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'status']):
            try:
                nombre = (proc.info['name'] or "").lower()
                if proc.info['status'] == psutil.STATUS_STOPPED or not nombre: 
                    continue
                if nombre in self.lista_blanca: 
                    continue
                if proc.info['memory_info'] is None: 
                    continue
                
                mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                if nombre not in apps_agrupadas:
                    apps_agrupadas[nombre] = {'pids': [], 'ram': 0}
                apps_agrupadas[nombre]['pids'].append(proc.info['pid'])
                apps_agrupadas[nombre]['ram'] += mem_mb
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
        
        self.datos_escaneo_actual = [
            {"exe": n, "pids_count": len(d['pids']), "ram": d['ram'], "pids": d['pids']}
            for n, d in apps_agrupadas.items() if d['ram'] > 1
        ]
        self.datos_escaneo_actual.sort(key=lambda x: x['ram'], reverse=True)
        self.after(0, self.mostrar_datos_tabla)

    def mostrar_datos_tabla(self):
        """Vuelca la telemetría recolectada en la Grid View aplicando los estilos visuales de la IA."""
        for item in self.tabla_activas.get_children():
            self.tabla_activas.delete(item)
            
        for d in self.datos_escaneo_actual:
            exe = d['exe']
            candado = "🔒" if exe in self.apps_excluidas else "🔓"
            estado_ia = self.categorias_ia.get(exe, "Pendiente")
            
            if exe in self.procesos_bloqueados:
                tag = "bloqueado"
            else:
                tag = estado_ia.lower() if estado_ia.lower() in ["critico", "seguro", "sospechoso"] else "sospechoso"
                
            self.tabla_activas.insert(
                "", 
                "end", 
                values=(candado, self.nombres_amigables.get(exe, exe), exe, d['pids_count'], f"{d['ram']:.1f} MB", estado_ia), 
                tags=(tag,)
            )
        self.actualizar_vista_guardian()

    def alternar_exclusion_candado(self, event=None):
        """Agrega o remueve una aplicación de la lista de exclusión (Lista Blanca del Usuario) con doble clic."""
        sel = self.tabla_activas.selection()
        if not sel:
            return
        exe = self.tabla_activas.item(sel[0], "values")[2]
        if exe in self.apps_excluidas:
            self.apps_excluidas.remove(exe)
            self.log_consola(f"Protección removida para: {exe}")
        else:
            self.apps_excluidas.add(exe)
            self.log_consola(f"Protección activada (Candado cerrado) para: {exe}")
        self.guardar_configuracion()
        self.mostrar_datos_tabla()

    def suspender_app(self):
        """Detiene de forma temporal los hilos de ejecución de un proceso para liberar CPU sin perder su estado."""
        sel = self.tabla_activas.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecciona una aplicación activa de la tabla.")
        exe = self.tabla_activas.item(sel[0], "values")[2]
        
        if exe in self.apps_excluidas:
            return messagebox.showerror("Error", "Esta aplicación está protegida por candado. Quita el candado antes de suspenderla.")
            
        pids_afectados = []
        for d in self.datos_escaneo_actual:
            if d['exe'] == exe:
                pids_afectados = d['pids']
                break
                
        exito = False
        for pid in pids_afectados:
            try:
                proc = psutil.Process(pid)
                proc.suspend()
                exito = True
            except Exception:
                continue
                
        if exito:
            self.procesos_suspendidos[exe] = pids_afectados
            self.log_consola(f"⏸️ Aplicación suspendida con éxito: {exe} (PIDs: {pids_afectados})")
            self.iniciar_escaneo()
        else:
            messagebox.showerror("Error", f"No se pudo suspender el proceso {exe}. Puede requerir privilegios del sistema.")

    def matar_app(self):
        """Termina de raíz y de manera forzada la ejecución del árbol de procesos seleccionado."""
        sel = self.tabla_activas.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecciona una aplicación de la lista.")
        exe = self.tabla_activas.item(sel[0], "values")[2]
        
        if exe in self.apps_excluidas:
            return messagebox.showerror("Error", "Operación cancelada: El proceso está protegido por exclusión de candado.")
            
        pids_afectados = []
        for d in self.datos_escaneo_actual:
            if d['exe'] == exe:
                pids_afectados = d['pids']
                break
                
        for pid in pids_afectados:
            try:
                proc = psutil.Process(pid)
                proc.kill()
            except Exception:
                continue
                
        self.log_consola(f"💀 Forzado de cierre total ejecutado en: {exe}")
        self.iniciar_escaneo()

    def reanudar_app(self):
        """Descongela la ejecución de una aplicación previamente enviada al módulo Guardián."""
        sel = self.tabla_suspendidas.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecciona una aplicación suspendida de la lista.")
        exe = self.tabla_suspendidas.item(sel[0], "values")[0]
        
        pids = self.procesos_suspendidos.get(exe, [])
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                proc.resume()
            except Exception:
                continue
                
        if exe in self.procesos_suspendidos:
            del self.procesos_suspendidos[exe]
            
        self.log_consola(f"▶️ Aplicación reanudada por el usuario: {exe}")
        self.iniciar_escaneo()

    def alternar_regla_guardian(self):
        """Establece o revoca una directiva de auto-bloqueo/auto-suspensión persistente sobre un ejecutable."""
        sel = self.tabla_suspendidas.selection()
        exe = ""
        if sel:
            exe = self.tabla_suspendidas.item(sel[0], "values")[0]
        else:
            sel_activa = self.tabla_activas.selection()
            if not sel_activa:
                return messagebox.showwarning("Aviso", "Selecciona una aplicación en cualquiera de las pestañas para configurar su regla.")
            exe = self.tabla_activas.item(sel_activa[0], "values")[2]
            
        if exe in self.reglas_guardian:
            del self.reglas_guardian[exe]
            self.log_consola(f"Regla Guardián eliminada para: {exe}")
        else:
            self.reglas_guardian[exe] = "Auto-Suspender"
            self.log_consola(f"🛡️ Guardián asignó regla de 'Auto-Suspender' para: {exe}")
            
        self.guardar_configuracion()
        self.iniciar_escaneo()

    def actualizar_vista_guardian(self):
        """Refresca la cuadrícula del Guardián mapeando el estado de memoria real contra las reglas."""
        for item in self.tabla_suspendidas.get_children():
            self.tabla_suspendidas.delete(item)
            
        # Sincronizar procesos actualmente congelados
        for exe, pids in self.procesos_suspendidos.items():
            self.tabla_suspendidas.insert("", "end", values=(exe, "CONGELADO (RAM Libre)", self.reglas_guardian.get(exe, "Ninguna")))
            
        # Mostrar reglas pasivas
        for exe, regla in self.reglas_guardian.items():
            if exe not in self.procesos_suspendidos:
                self.tabla_suspendidas.insert("", "end", values=(exe, "Monitoreando Pasivo", regla))

    def verificar_guardian(self):
        """Demonio en segundo plano (Watchdog) que aplica de forma automática las reglas del Guardián."""
        if hasattr(self, 'reglas_guardian') and self.reglas_guardian:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    nombre = (proc.info['name'] or "").lower()
                    if nombre in self.reglas_guardian and nombre not in self.apps_excluidas:
                        regla = self.reglas_guardian[nombre]
                        if regla == "Auto-Suspender" and nombre not in self.procesos_suspendidos:
                            proc.suspend()
                            if nombre not in self.procesos_suspendidos:
                                self.procesos_suspendidos[nombre] = [proc.info['pid']]
                            else:
                                if proc.info['pid'] not in self.procesos_suspendidos[nombre]:
                                    self.procesos_suspendidos[nombre].append(proc.info['pid'])
                            self.log_consola(f"[GUARDIÁN AUTOMÁTICO] Se interceptó y suspendió: {nombre}")
                except Exception:
                    continue
        self.after(3000, self.verificar_guardian)

    def analizar_con_ia(self):
        """Clasifica por lotes los procesos en ejecución interactuando de forma masiva con Gemini."""
        if not self.datos_escaneo_actual:
            return messagebox.showwarning("Aviso", "No hay procesos detectados para analizar.")
            
        def hilo_analisis():
            self.log_consola("🧠 [IA Core] Iniciando categorización masiva de procesos activos...")
            lista_exes = [d['exe'] for d in self.datos_escaneo_actual[:15]] # Top 15 consumidores
            
            prompt = (
                f"Analiza esta lista de ejecutables de Windows: {lista_exes}. "
                f"Devuelve estrictamente un objeto JSON plano donde cada clave sea el ejecutable "
                f"y su valor sea ÚNICAMENTE uno de estos tres estados de riesgo: 'Seguro', 'Sospechoso' o 'Critico'. "
                f"No agregues texto Markdown ni explicaciones prose."
            )
            try:
                respuesta, _ = self.ejecutar_consulta_gemini_cascada(prompt)
                # Limpieza de envolturas de código generadas habitualmente por modelos LLM
                json_limpio = respuesta.replace("```json", "").replace("```", "").strip()
                dict_res = json.loads(json_limpio)
                
                for exe, estado in dict_res.items():
                    self.categorias_ia[exe.lower()] = estado
                    
                self.guardar_configuracion()
                self.after(0, lambda: [self.mostrar_datos_tabla(), messagebox.showinfo("Éxito", "Procesos categorizados por IA correctamente.")])
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error IA", f"Fallo al procesar lote: {e}"))
                
        threading.Thread(target=hilo_analisis, daemon=True).start()

    def ejecutar_perfil_ia(self):
        """Aplica políticas automáticas agresivas o pasivas sobre la RAM según el perfil seleccionado."""
        perfil = self.combo_perfiles.get()
        self.log_consola(f"⚡ Aplicando política de optimización: {perfil}")
        
        count = 0
        for d in list(self.datos_escaneo_actual):
            exe = d['exe']
            if exe in self.apps_excluidas or exe in self.lista_blanca:
                continue
                
            estado_ia = self.categorias_ia.get(exe, "Sospechoso")
            
            if perfil == "Modo Gamer (Suspender)":
                if estado_ia in ["Sospechoso", "Critico"] or d['ram'] > 150:
                    for pid in d['pids']:
                        try:
                            psutil.Process(pid).suspend()
                        except Exception:
                            continue
                    self.procesos_suspendidos[exe] = d['pids']
                    count += 1
                    
            elif perfil == "Modo Turbo (Cierre)":
                if estado_ia in ["Sospechoso", "Critico"] or d['ram'] > 80:
                    for pid in d['pids']:
                        try:
                            psutil.Process(pid).kill()
                        except Exception:
                            continue
                    count += 1
                    
        self.log_consola(f"✅ Optimización completada. {count} aplicaciones procesadas por la directiva.")
        self.iniciar_escaneo()

    def leer_programas_inicio(self):
        """Inspecciona las colas de las llaves del registro de Windows para listar los arranques."""
        for item in self.tabla_inicio.get_children():
            self.tabla_inicio.delete(item)
            
        rutas_registro = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "User Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Local Machine Run")
        ]
        
        for hkey, subkey, ub in rutas_registro:
            try:
                key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
                count = winreg.QueryInfoKey(key)[1]
                for i in range(count):
                    nombre, comando, _ = winreg.EnumValue(key, i)
                    self.tabla_inicio.insert("", "end", values=(nombre, comando, ub))
                winreg.CloseKey(key)
            except Exception:
                continue

    def deshabilitar_programa_inicio(self):
        """Purga un disparador de ejecución automática removiendo su valor del registro NT."""
        sel = self.tabla_inicio.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecciona un elemento de la lista de arranque.")
        valores = self.tabla_inicio.item(sel[0], "values")
        nombre = valores[0]
        ub = valores[2]
        
        hkey = winreg.HKEY_CURRENT_USER if "User" in ub else winreg.HKEY_LOCAL_MACHINE
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, nombre)
            winreg.CloseKey(key)
            self.log_consola(f"🚀 Eliminado del inicio del sistema: {nombre}")
            self.leer_programas_inicio()
        except Exception as e:
            messagebox.showerror("Error", f"Falta de privilegios para editar el registro NT: {e}")

    def listar_servicios_windows(self):
        """Interroga la API win_service de psutil para mapear los servicios del sistema operativo."""
        for item in self.tabla_servicios.get_children():
            self.tabla_servicios.delete(item)
            
        try:
            for service in psutil.win_service_iter():
                try:
                    info = service.as_dict()
                    self.tabla_servicios.insert(
                        "", 
                        "end", 
                        values=(info['name'], info['display_name'], info['status'], info['start_type'])
                    )
                except Exception:
                    continue
        except Exception as e:
            self.log_consola(f"No se pudieron enumerar los servicios NT: {e}")

    def deshabilitar_servicio_windows(self):
        """Modifica el comportamiento y detiene un servicio NT invocando comandos elevados de shell."""
        if not es_administrador():
            return messagebox.showerror("Denegado", "Esta acción requiere obligatoriamente privilegios de Administrador.")
            
        sel = self.tabla_servicios.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecciona un servicio de la tabla.")
        service_name = self.tabla_servicios.item(sel[0], "values")[0]
        
        try:
            subprocess.run(f'sc config "{service_name}" start= disabled', shell=True, check=True, capture_output=True)
            subprocess.run(f'sc stop "{service_name}"', shell=True, capture_output=True)
            self.log_consola(f"⚙️ Servicio deshabilitado y parado exitosamente: {service_name}")
            self.listar_servicios_windows()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Fallo al alterar configuración de SC.exe: {e.stderr.decode('cp1252', errors='ignore')}")

# ==============================================================================
# 🚀 SECCIÓN 7: LÓGICA SYSADMIN (Bloatware, Telemetría, Tareas)
# ==============================================================================
    def refrescar_todo_el_sistema(self):
        """Dispara de manera asíncrona la recolección integral de telemetría de componentes,

        aplicaciones del sistema y colas de automatización en segundo plano."""
        self.log_consola("Escaneando subsistemas operacionales de Windows...")
        threading.Thread(target=self._hilo_escaneo_sistema, daemon=True).start()

    def _hilo_escaneo_sistema(self):
        """Módulo recolector multihilo. Interroga registros, servicios nativos y

        el planificador de tareas para mapear el estado de optimización del SO."""
        
        # 1. ESCANEO PROFUNDO DE REGISTRO NT (Mapeo Completo de Bloatware de 32 y 64 bits)
        self.datos_bloatware = []
        rutas_registro = [
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall", 0)
        ]
        
        visitados = set()
        for hkey, sub_ruta, banderas in rutas_registro:
            try:
                acceso = winreg.KEY_READ | banderas
                with winreg.OpenKey(hkey, sub_ruta, 0, acceso) as key:
                    num_subclaves = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subclaves):
                        try:
                            sub_llave = winreg.EnumKey(key, i)
                            if sub_llave in visitados:
                                continue
                            
                            with winreg.OpenKey(key, sub_llave) as s_key:
                                try:
                                    dn, _ = winreg.QueryValueEx(s_key, "DisplayName")
                                    if not dn or not str(dn).strip():
                                        continue
                                except FileNotFoundError:
                                    continue
                                
                                try:
                                    pub, _ = winreg.QueryValueEx(s_key, "Publisher")
                                except FileNotFoundError:
                                    pub = "Desconocido o Sistema"
                                    
                                self.datos_bloatware.append({
                                    "id": sub_llave, 
                                    "nombre": str(dn).strip(), 
                                    "editor": str(pub).strip()
                                })
                                visitados.add(sub_llave)
                        except Exception:
                            continue
            except Exception:
                continue

        # 2. TELEMETRÍA CORE (Detección Segura de Servicios Críticos de Recolección de Datos)
        self.datos_telemetria = []
        servicios_rastreo = ['DiagTrack', 'SysMain', 'dmwappushservice', 'WerSvc']
        
        for s in servicios_rastreo:
            try:
                srv_instancia = psutil.win_service_get(s)
                status = srv_instancia.status()
                estado_legible = "Activo" if status == "running" else "Detenido"
                self.datos_telemetria.append({"nombre": s, "estado": estado_legible})
            except psutil.NoSuchProcess:
                # El servicio no se encuentra instalado en esta SKU o edición de Windows
                continue
            except Exception:
                continue

        # 3. TAREAS PROGRAMADAS (Escaneo completo a prueba de fallos)
        self.datos_tareas = []
        try:
            # Añadimos -ErrorAction SilentlyContinue para evitar que las tareas protegidas bloqueen el escaneo
            cmd = 'powershell -NoProfile -Command "Get-ScheduledTask -ErrorAction SilentlyContinue | Select-Object TaskPath, TaskName, State | ConvertTo-Json -Compress"'
            proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
            
            # Verificamos si hay contenido (stdout) independientemente del código de salida (returncode)
            if proc.stdout and proc.stdout.strip().startswith(('{', '[')):
                items = json.loads(proc.stdout.strip())
                
                # Forzar encapsulado en lista si el parser retorna un diccionario único
                if isinstance(items, dict):
                    items = [items]
                    
                if items:
                    for it in items:
                        nombre_tarea = it.get("TaskName", "")
                        if nombre_tarea:
                            estado_raw = it.get("State")
                            
                            # Mapeo exhaustivo de los estados reales de Windows
                            if estado_raw == 1 or str(estado_raw).lower() == "disabled":
                                estado_txt = "Deshabilitada"
                            elif estado_raw == 2 or str(estado_raw).lower() == "queued":
                                estado_txt = "En cola"
                            elif estado_raw == 3 or str(estado_raw).lower() == "ready":
                                estado_txt = "Lista"
                            elif estado_raw == 4 or str(estado_raw).lower() == "running":
                                estado_txt = "En ejecución"
                            else:
                                estado_txt = "Desconocido"

                            self.datos_tareas.append({
                                "ruta": it.get("TaskPath", "\\"), 
                                "nombre": nombre_tarea, 
                                "estado": estado_txt
                            })
        except Exception as e:
            self.log_consola(f"Aviso no crítico al interrogar SchTasks: {str(e)}")
            
        # Redireccionar el volcado de la estructura final al hilo principal de la UI
        self.after(0, self._renderizar_tablas_locales)

    def _renderizar_tablas_locales(self):
        """Vuelca de forma segura las estructuras cacheadas del sistema en las vistas TreeView."""
        for t in [self.tabla_bloatware, self.tabla_telemetria, self.tabla_tareas]:
            if t.winfo_exists():
                for item in t.get_children():
                    t.delete(item)

        # Poblar Grid View de Aplicaciones / Bloatware
        for app in self.datos_bloatware:
            rec = self.cache_ia.get(app["id"], "Pendiente")
            tag = rec.lower() if rec.lower() in ["critico", "sospechoso", "seguro"] else "seguro"
            self.tabla_bloatware.insert("", "end", values=(app["id"], app["nombre"], app["editor"], rec), tags=(tag,))

        # Poblar Grid View de Servicios de Telemetría
        for serv in self.datos_telemetria:
            rec = self.cache_ia.get(serv["nombre"], "Pendiente")
            tag = "critico" if rec == "Critico" or serv["nombre"] in ['DiagTrack', 'dmwappushservice'] else "seguro"
            self.tabla_telemetria.insert("", "end", values=(serv["nombre"], "Servicio Automatizado NT", serv["estado"], rec), tags=(tag,))

        # Poblar Grid View de Tareas Programadas
        for tar in self.datos_tareas:
            rec = self.cache_ia.get(tar["nombre"], "Pendiente")
            tag = rec.lower() if rec.lower() in ["critico", "sospechoso", "seguro"] else "seguro"
            self.tabla_tareas.insert("", "end", values=(tar["ruta"], tar["nombre"], tar["estado"], rec), tags=(tag,))
            
        self.log_consola("🔄 Subsistemas sincronizados e indexados en el panel de control.")

    def analizar_sistema_con_ia(self):
        """Inicia el escaneo predictivo de telemetría masiva interactuando de forma controlada con Gemini."""
        if hasattr(self, 'ia_en_progreso') and self.ia_en_progreso:
            return messagebox.showinfo("Info", "Existe un diagnóstico heurístico de la IA ejecutándose actualmente.")
            
        self.ia_en_progreso = True
        self.log_consola("🧠 [SysAdmin IA] Generando paquete estructurado y transmitiendo lote a Gemini...")
        threading.Thread(target=self._hilo_ia_profunda, daemon=True).start()

    def _hilo_ia_profunda(self):
        """Empaqueta telemetría local, interroga la cascada LLM y actualiza el buffer de persistencia."""
        try:
            # Recorte y optimización de tokens para la ventana de contexto (Top 30 Apps)
            datos_paquete = {
                "apps": [{"id": a["id"], "nombre": a["nombre"]} for a in self.datos_bloatware[:30]], 
                "servicios": [s["nombre"] for s in self.datos_telemetria], 
                "tareas": [t["nombre"] for t in self.datos_tareas[:20]]
            }
            
            prompt = (
                f"Analiza los siguientes elementos de software/configuración de Windows: {json.dumps(datos_paquete)}. "
                f"Determina su impacto en la privacidad y rendimiento. Retorna EXCLUSIVAMENTE un objeto JSON plano "
                f"con la siguiente estructura estricta de llaves: "
                f"{{\"apps\":[{{\"id\":\"id_real\", \"accion\":\"Critico/Sospechoso/Seguro\"}}], "
                f"\"servicios\":[{{\"nombre\":\"nombre_real\", \"accion\":\"Critico/Seguro\"}}], "
                f"\"tareas\":[{{\"nombre\":\"nombre_real\", \"accion\":\"Critico/Sospechoso/Seguro\"}}]}}. "
                f"No incluyas texto explicativo, preámbulos ni bloques de marcas markdown."
            )
            
            respuesta, modelo_usado = self.ejecutar_consulta_gemini_cascada(prompt)
            
            # Sanitización de la respuesta cruda del LLM
            json_limpio = respuesta.strip().replace('```json', '').replace('```', '').strip()
            datos_ia = json.loads(json_limpio)
            
            # Actualización centralizada del mapping en memoria caché
            for d in datos_ia.get("apps", []):
                if d.get("id"):
                    self.cache_ia[d.get("id")] = d.get("accion", "Seguro")
            for d in datos_ia.get("servicios", []):
                if d.get("nombre"):
                    self.cache_ia[d.get("nombre")] = d.get("accion", "Seguro")
            for d in datos_ia.get("tareas", []):
                if d.get("nombre"):
                    self.cache_ia[d.get("nombre")] = d.get("accion", "Seguro")
            
            # Sincronización en disco duro (JSON persistente unificado)
            self.guardar_configuracion()
            self.ia_en_progreso = False
            self.after(0, lambda: [self._renderizar_tablas_locales(), self.log_consola(f"🧠 Diagnóstico SysAdmin finalizado exitosamente usando {modelo_usado}.")])
            
        except Exception as e:
            self.ia_en_progreso = False
            self.after(0, lambda: self.log_consola(f"⚠️ Error en el procesamiento del flujo SysAdmin IA: {str(e)}"))

    def ejecutar_desinstalacion_bloatware(self):
        """Invoca al gestor nativo de paquetes de Windows (Winget) para purgar de raíz el software redundante."""
        sel = self.tabla_bloatware.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecciona una aplicación de la lista de bloatware detectado.")
            
        valores = self.tabla_bloatware.item(sel[0], "values")
        id_app = valores[0]
        nombre_app = valores[1]
        
        if messagebox.askyesno("Confirmar acción", f"¿Estás seguro de que deseas purgar de forma silenciosa la aplicación '{nombre_app}' a través de Windows Winget?"):
            self.log_consola(f"🛒 Purgando instalador [{nombre_app}] mediante canal silencioso Winget...")
            
            def hilo_purgar():
                try:
                    # Intento prioritario por ID único de paquete para evitar ambigüedades, caída en cascada por nombre alternativo
                    cmd = f'winget uninstall --id "{id_app}" --silent --accept-source-agreements'
                    resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
                    
                    if resultado.returncode != 0:
                        cmd_alt = f'winget uninstall --name "{nombre_app}" --silent --accept-source-agreements'
                        subprocess.run(cmd_alt, shell=True, capture_output=True, timeout=120)
                        
                    self.after(0, lambda: [self.log_consola(f"💀 Ejecución de desinstalación completada para: {nombre_app}"), self.refrescar_todo_el_sistema()])
                except subprocess.TimeoutExpired:
                    self.after(0, lambda: self.log_consola(f"⚠️ El proceso Winget para '{nombre_app}' excedió el límite de tiempo."))
                except Exception as e:
                    self.after(0, lambda: self.log_consola(f"⚠️ Error inesperado al desinstalar: {str(e)}"))
                    
            threading.Thread(target=hilo_purgar, daemon=True).start()

    def ejecutar_bloqueo_telemetria(self):
        """Detiene y bloquea el arranque de servicios de rastreo del sistema operativo."""
        sel = self.tabla_telemetria.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecciona un servicio de la lista de telemetría.")
            
        srv_nombre = self.tabla_telemetria.item(sel[0], "values")[0]
        self.log_consola(f"🛡️ Neutralizando servicio de telemetría del sistema operativo: {srv_nombre}...")
        
        def hilo_servicio():
            try:
                # Modificación forzada y atómica mediante llamadas directas a SC del núcleo de Windows
                cmd = f'sc stop "{srv_nombre}" & sc config "{srv_nombre}" start= disabled'
                subprocess.run(cmd, shell=True, capture_output=True, text=True)
                self.after(0, lambda: [self.log_consola(f"🔒 Canal de telemetría '{srv_nombre}' bloqueado permanentemente."), self.refrescar_todo_el_sistema()])
            except Exception as e:
                self.after(0, lambda: self.log_consola(f"⚠️ Error al mitigar servicio NT: {str(e)}"))
                
        threading.Thread(target=hilo_servicio, daemon=True).start()

    def ejecutar_desactivacion_tarea(self):
        """Deshabilita de forma definitiva disparadores automatizados de rastreo en SchTasks."""
        sel = self.tabla_tareas.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecciona una tarea programada de la cuadrícula.")
            
        valores = self.tabla_tareas.item(sel[0], "values")
        ruta_tarea = valores[0]
        nombre_tarea = valores[1]
        
        # Normalización matemática de rutas en el planificador (evitar duplicado de diagonales invertidas)
        if str(ruta_tarea).endswith("\\"):
            ruta_completa = f"{ruta_tarea}{nombre_tarea}"
        else:
            ruta_completa = f"{ruta_tarea}\\{nombre_tarea}"
            
        self.log_consola(f"🛡️ Desactivando regla de ejecución automática: {nombre_tarea}...")
        
        def hilo_tarea():
            try:
                cmd = f'schtasks /change /tn "{ruta_completa}" /disable'
                resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if resultado.returncode == 0:
                    self.after(0, lambda: [self.log_consola(f"✅ Tarea mitigada con éxito: {nombre_tarea}"), self.refrescar_todo_el_sistema()])
                else:
                    self.after(0, lambda: self.log_consola(f"⚠️ SchTasks rechazó la solicitud (Falta de privilegios NT Authority o tarea inexistente)."))
            except Exception as e:
                self.after(0, lambda: self.log_consola(f"⚠️ Error al operar SchTasks: {str(e)}"))
                
        threading.Thread(target=hilo_tarea, daemon=True).start()

    def analizar_tareas_con_ia(self):
        """Lanza el escaneo exclusivo para tareas programadas mediante procesamiento por lotes."""
        if hasattr(self, 'ia_en_progreso') and self.ia_en_progreso:
            return messagebox.showinfo("Info", "Existe un diagnóstico heurístico de la IA ejecutándose actualmente.")
            
        self.ia_en_progreso = True
        self.log_consola("🧠 [IA Tareas] Iniciando análisis inteligente de tareas programadas...")
        threading.Thread(target=self._hilo_ia_tareas, daemon=True).start()

    def _hilo_ia_tareas(self):
        """Procesa la lista de tareas en lotes para evitar la saturación del modelo LLM."""
        try:
            # 1. Filtrar solo las tareas que aún están en estado "Pendiente" para ahorrar tokens
            tareas_pendientes = [t["nombre"] for t in self.datos_tareas if self.cache_ia.get(t["nombre"], "Pendiente") == "Pendiente"]
            
            if not tareas_pendientes:
                self.ia_en_progreso = False
                self.after(0, lambda: messagebox.showinfo("IA", "Todas las tareas ya han sido categorizadas previamente."))
                return
                
            # 2. Configurar el tamaño del lote (Chunking: 30 tareas por cada llamada a Gemini)
            tamaño_lote = 30
            lotes = [tareas_pendientes[i:i + tamaño_lote] for i in range(0, len(tareas_pendientes), tamaño_lote)]
            
            self.after(0, lambda: self.log_consola(f"🧠 [IA Tareas] Se analizarán {len(tareas_pendientes)} tareas en {len(lotes)} lote(s)."))
            
            for idx, lote in enumerate(lotes):
                self.after(0, lambda i=idx: self.log_consola(f"🧠 [IA Tareas] Procesando lote {i+1} de {len(lotes)}..."))
                
                prompt = (
                    f"Analiza esta lista de tareas programadas de Windows: {json.dumps(lote)}. "
                    f"Determina su riesgo o si son prescindibles. Retorna EXCLUSIVAMENTE un objeto JSON plano "
                    f"donde la clave sea el nombre exacto de la tarea y el valor sea ÚNICAMENTE "
                    f"'Critico', 'Sospechoso' o 'Seguro'. No agregues texto markdown, ni explicaciones."
                )
                
                respuesta, modelo_usado = self.ejecutar_consulta_gemini_cascada(prompt)
                
                # Sanitización estricta
                json_limpio = respuesta.strip().replace('```json', '').replace('```', '').strip()
                datos_ia = json.loads(json_limpio)
                
                # Actualización de la caché con los resultados del lote
                for nombre_tarea, estado in datos_ia.items():
                    self.cache_ia[nombre_tarea] = estado
                    
                # 3. Guardar persistencia y refrescar tabla visualmente tras cada lote
                self.guardar_configuracion()
                self.after(0, self._renderizar_tablas_locales)
                
            self.ia_en_progreso = False
            self.after(0, lambda: self.log_consola("✅ [IA Tareas] Análisis masivo de tareas finalizado con éxito."))
            
        except Exception as e:
            self.ia_en_progreso = False
            self.after(0, lambda: self.log_consola(f"⚠️ Error en el procesamiento de IA para tareas: {str(e)}"))

if __name__ == "__main__":
    # Inicializador estándar del módulo para asegurar la compatibilidad del compilador nativo de Windows
    app = W11RamOptimizer()
    app.mainloop()