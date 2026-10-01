import customtkinter as ctk

from vistas.vista_admin import VistaAdmin
from vistas.vista_profesor import VistaProfesor
from vistas.vista_estudiante import VistaEstudiante
from vistas.vista_admin_cursos import VistaAdminCursos
from vistas.vista_admin_institucion import VistaAdminInstitucion
from vistas.vista_admin_profesores import VistaAdminProfesores
from vistas.vista_admin_secciones import VistaAdminSecciones

BG_COLOR = "#282828"
SIDEBAR_COLOR = "#3c3836"
ACCENT_COLOR = "#d79921"
TEXT_COLOR = "#ebdbb2"

class AulaVirtualApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Aula Virtual - Gestión Académica")
        self.geometry("1100x700")
        self.configure(fg_color=BG_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.vista_actual = None

        # -- SIDEBAR --
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1) 

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Aula Virtual", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT_COLOR)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Selector de Rol
        lbl_rol = ctk.CTkLabel(self.sidebar_frame, text="Cambiar Rol de Sesión:", text_color=TEXT_COLOR, font=ctk.CTkFont(size=12))
        lbl_rol.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.selector_rol = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            values=["Administrador", "Profesor", "Estudiante"],
            command=self.cambiar_vista,
            fg_color=BG_COLOR,
            button_color=ACCENT_COLOR,
            button_hover_color="#b57614"
        )
        self.selector_rol.grid(row=2, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Separador visual
        separador = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color=BG_COLOR)
        separador.grid(row=3, column=0, sticky="ew", padx=20, pady=5)

        # Contenedor dinámico para las Pestañas/Submenús
        self.frame_submenu = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.frame_submenu.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)

        # Iniciar por defecto en Administrador
        self.cambiar_vista("Administrador")

    def cambiar_vista(self, rol_seleccionado):
        # 1. Limpiar la vista principal
        if self.vista_actual is not None:
            self.vista_actual.destroy()

        # 2. Limpiar el submenú lateral
        for widget in self.frame_submenu.winfo_children():
            widget.destroy()

        # 3. Cargar la nueva vista y sus botones respectivos
        if rol_seleccionado == "Administrador":
            self.vista_actual = VistaAdmin(self)
            self.crear_boton_submenu("🎓 Estudiantes", lambda: self.cargar_vista_admin_estudiantes())
            self.crear_boton_submenu("👨‍🏫 Profesores", lambda: self.cargar_vista_admin_profesores())
            self.crear_boton_submenu("📚 Cursos", lambda: self.cargar_vista_admin_cursos())
            self.crear_boton_submenu("🏫 Secciones", lambda: self.cargar_vista_admin_secciones())
            self.crear_boton_submenu("⚙️ Institución", lambda: self.cargar_vista_admin_institucion())
            
        elif rol_seleccionado == "Profesor":
            self.vista_actual = VistaProfesor(self)
            self.crear_boton_submenu("📅 Mi Portal Docente", lambda: self.cargar_vista_profesor())

        elif rol_seleccionado == "Estudiante":
            self.vista_actual = VistaEstudiante(self)
            self.crear_boton_submenu("🎓 Mi Portal", lambda: self.cargar_vista_estudiante())

        # LÍNEA QUE DIBUJA LA PANTALLA
        self.vista_actual.grid(row=0, column=1, sticky="nsew")


    # --- MÉTODOS PARA CARGAR LAS VISTAS AL HACER CLIC EN LOS BOTONES ---

    def cargar_vista_admin_estudiantes(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = VistaAdmin(self)
        self.vista_actual.grid(row=0, column=1, sticky="nsew")

    def cargar_vista_admin_profesores(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = VistaAdminProfesores(self)
        self.vista_actual.grid(row=0, column=1, sticky="nsew")

    def cargar_vista_admin_cursos(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = VistaAdminCursos(self)
        self.vista_actual.grid(row=0, column=1, sticky="nsew")

    def cargar_vista_admin_secciones(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = VistaAdminSecciones(self)
        self.vista_actual.grid(row=0, column=1, sticky="nsew")

    def cargar_vista_admin_institucion(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = VistaAdminInstitucion(self)
        self.vista_actual.grid(row=0, column=1, sticky="nsew")

    def cargar_vista_profesor(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = VistaProfesor(self)
        self.vista_actual.grid(row=0, column=1, sticky="nsew")
        
    def cargar_vista_estudiante(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = VistaEstudiante(self)
        self.vista_actual.grid(row=0, column=1, sticky="nsew")

    def crear_boton_submenu(self, texto, comando):
        btn = ctk.CTkButton(
            self.frame_submenu, 
            text=texto, 
            fg_color="transparent", 
            text_color=TEXT_COLOR, 
            hover_color=BG_COLOR,
            anchor="w",
            font=ctk.CTkFont(size=14),
            command=comando
        )
        btn.pack(fill="x", pady=2, padx=10)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = AulaVirtualApp()
    app.mainloop()