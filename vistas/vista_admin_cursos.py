import customtkinter as ctk
import psycopg2
from conexion import conectar_bd

BG_COLOR = "#282828"
SIDEBAR_COLOR = "#3c3836"
ACCENT_COLOR = "#d79921"
TEXT_COLOR = "#ebdbb2"
RED_COLOR = "#cc241d"
GREEN_COLOR = "#98971a"

# ==========================================
# VENTANA MODAL: NUEVO CURSO
# ==========================================
class VentanaNuevoCurso(ctk.CTkToplevel):
    def __init__(self, master, callback_actualizar):
        super().__init__(master)
        self.title("Nuevo Curso")
        self.geometry("400x480")
        self.configure(fg_color=BG_COLOR)
        self.grab_set() 
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text="Registrar Materia", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_COLOR).pack(pady=15)

        self.ent_codigo = ctk.CTkEntry(self, placeholder_text="Código (Ej: MAT-101)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_codigo.pack(pady=10)

        self.ent_nombre = ctk.CTkEntry(self, placeholder_text="Nombre del Curso", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_nombre.pack(pady=10)

        self.ent_cupo = ctk.CTkEntry(self, placeholder_text="Cupo Máximo (Ej: 30)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_cupo.pack(pady=10)

        self.ent_costo = ctk.CTkEntry(self, placeholder_text="Costo ($)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_costo.pack(pady=10)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=5)

        btn_guardar = ctk.CTkButton(self, text="Guardar", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.guardar_bd)
        btn_guardar.pack(pady=10)

    def guardar_bd(self):
        codigo = self.ent_codigo.get().strip()
        nombre = self.ent_nombre.get().strip()
        cupo_str = self.ent_cupo.get().strip()
        costo_str = self.ent_costo.get().strip()

        if not all([codigo, nombre, cupo_str, costo_str]):
            self.lbl_error.configure(text="Todos los campos son obligatorios.")
            return

        try:
            cupo = int(cupo_str)
            costo = float(costo_str)
        except ValueError:
            self.lbl_error.configure(text="El cupo y costo deben ser numéricos.")
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("INSERT INTO curso (codigo, nombre, cupo_maximo, costo) VALUES (%s, %s, %s, %s)", (codigo, nombre, cupo, costo))
                conn.commit()
                self.callback_actualizar()
                self.destroy()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                self.lbl_error.configure(text="Error: Este código o nombre ya existe.")
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error inesperado: {e}")
            finally:
                cur.close()
                conn.close()

# ==========================================
# VENTANA MODAL: CONFIGURAR CURSO (Híbrida)
# ==========================================
class VentanaConfigurarCurso(ctk.CTkToplevel):
    def __init__(self, master, id_curso, callback_actualizar):
        super().__init__(master)
        self.title("Configuración de Curso")
        self.geometry("480x650")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()
        
        self.id_curso = id_curso
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text="Atributos Generales", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_COLOR).pack(pady=(15, 5))
        
        frame_datos = ctk.CTkFrame(self, fg_color="transparent")
        frame_datos.pack(padx=20, fill="x")

        self.ent_codigo = ctk.CTkEntry(frame_datos, placeholder_text="Código", width=140, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_codigo.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.ent_nombre = ctk.CTkEntry(frame_datos, placeholder_text="Nombre", width=280, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_nombre.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.ent_cupo = ctk.CTkEntry(frame_datos, placeholder_text="Cupo", width=140, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_cupo.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.ent_costo = ctk.CTkEntry(frame_datos, placeholder_text="Costo ($)", width=280, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_costo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkFrame(self, height=2, fg_color=SIDEBAR_COLOR).pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(self, text="Requisitos (Prelaciones)", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_COLOR).pack(pady=(5, 5))
        
        self.ent_busqueda = ctk.CTkEntry(self, placeholder_text="Buscar código o nombre...", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_busqueda.pack(pady=5)
        self.ent_busqueda.bind("<KeyRelease>", self.dibujar_lista)

        self.frame_lista = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.frame_lista.pack(padx=20, pady=5, fill="both", expand=True)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=GREEN_COLOR)
        self.lbl_error.pack(pady=5)

        btn_guardar = ctk.CTkButton(self, text="Guardar Configuración", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.guardar_cambios)
        btn_guardar.pack(pady=10)

        self.datos_cursos = [] 
        self.variables_check = {} 
        
        self.cargar_memoria()

    def cargar_memoria(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT codigo, nombre, cupo_maximo, costo FROM curso WHERE id_curso = %s", (self.id_curso,))
                curso_actual = cur.fetchone()
                if curso_actual:
                    self.ent_codigo.insert(0, curso_actual[0] if curso_actual[0] else "")
                    self.ent_nombre.insert(0, curso_actual[1])
                    self.ent_cupo.insert(0, str(curso_actual[2]))
                    self.ent_costo.insert(0, str(curso_actual[3]))

                cur.execute("SELECT id_curso, codigo, nombre FROM curso WHERE id_curso != %s ORDER BY codigo", (self.id_curso,))
                self.datos_cursos = cur.fetchall()

                # CORRECCIÓN: Vuelve a ser id_curso
                cur.execute("SELECT id_curso_requisito FROM prelacion WHERE id_curso = %s", (self.id_curso,))
                requisitos_actuales = [fila[0] for fila in cur.fetchall()]

                for id_req, codigo, nombre in self.datos_cursos:
                    self.variables_check[id_req] = ctk.BooleanVar(value=(id_req in requisitos_actuales))

                self.dibujar_lista()
            except Exception as e:
                self.lbl_error.configure(text=f"Error: {e}", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()

    def dibujar_lista(self, event=None):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        termino = self.ent_busqueda.get().strip().lower()

        for id_req, codigo, nombre in self.datos_cursos:
            texto_mostrar = f"{codigo} - {nombre}"
            if termino in texto_mostrar.lower() or termino == "":
                chk = ctk.CTkCheckBox(self.frame_lista, text=texto_mostrar, variable=self.variables_check[id_req], text_color=TEXT_COLOR, fg_color=ACCENT_COLOR, hover_color="#b57614")
                chk.pack(anchor="w", padx=10, pady=5)

    def guardar_cambios(self):
        codigo = self.ent_codigo.get().strip()
        nombre = self.ent_nombre.get().strip()
        cupo_str = self.ent_cupo.get().strip()
        costo_str = self.ent_costo.get().strip()

        if not all([codigo, nombre, cupo_str, costo_str]):
            self.lbl_error.configure(text="Atributos del curso obligatorios.", text_color=RED_COLOR)
            return

        try:
            cupo = int(cupo_str)
            costo = float(costo_str)
        except ValueError:
            self.lbl_error.configure(text="Cupo y costo deben ser numéricos.", text_color=RED_COLOR)
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute(
                    "UPDATE curso SET codigo=%s, nombre=%s, cupo_maximo=%s, costo=%s WHERE id_curso=%s",
                    (codigo, nombre, cupo, costo, self.id_curso)
                )

                # CORRECCIÓN: Vuelve a ser id_curso
                cur.execute("DELETE FROM prelacion WHERE id_curso = %s", (self.id_curso,))
                for id_req, var in self.variables_check.items():
                    if var.get():
                        cur.execute("INSERT INTO prelacion (id_curso, id_curso_requisito) VALUES (%s, %s)", (self.id_curso, id_req))
                conn.commit()
                self.lbl_error.configure(text="¡Configuración guardada con éxito!", text_color=GREEN_COLOR)
                self.callback_actualizar()
                self.after(1000, self.destroy) 
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                self.lbl_error.configure(text="Error: El código o nombre ya existe en otra materia.", text_color=RED_COLOR)
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error al guardar: {e}", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()

# ==========================================
# PANEL PRINCIPAL: VISTA CURSOS
# ==========================================
class VistaAdminCursos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_COLOR)
        
        self.titulo = ctk.CTkLabel(self, text="Catálogo de Cursos", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.titulo.pack(pady=(20, 10))

        frame_controles = ctk.CTkFrame(self, fg_color="transparent")
        frame_controles.pack(fill="x", padx=20, pady=10)

        self.btn_listar = ctk.CTkButton(frame_controles, text="Recargar", width=90, fg_color=ACCENT_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.cargar_cursos)
        self.btn_listar.pack(side="left", padx=5)

        self.btn_nuevo = ctk.CTkButton(frame_controles, text="+ Nuevo Curso", width=120, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=self.abrir_modal_nuevo)
        self.btn_nuevo.pack(side="left", padx=5)

        ctk.CTkLabel(frame_controles, text="Carrera:", text_color=TEXT_COLOR).pack(side="left", padx=(15, 2))
        self.combo_filtro = ctk.CTkOptionMenu(frame_controles, width=160, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.cargar_cursos)
        self.combo_filtro.pack(side="left", padx=5)
        self.cargar_opciones_filtro()

        ctk.CTkLabel(frame_controles, text="Buscar:", text_color=TEXT_COLOR).pack(side="left", padx=(15, 2))
        self.ent_busqueda = ctk.CTkEntry(frame_controles, placeholder_text="Código o Nombre...", width=150, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_busqueda.pack(side="left", padx=5)
        self.ent_busqueda.bind("<Return>", lambda event: self.cargar_cursos())

        self.tabla_frame = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.tabla_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        self.tabla_frame.grid_columnconfigure(6, weight=0)

    def cargar_opciones_filtro(self):
        conn, cur = conectar_bd()
        opciones = ["Todas"]
        if conn:
            try:
                cur.execute("SELECT nombre FROM carrera ORDER BY nombre;")
                opciones.extend([c[0] for c in cur.fetchall()])
            except Exception as e:
                print("Error cargando filtro:", e)
            finally:
                cur.close()
                conn.close()
        self.combo_filtro.configure(values=opciones)
        self.combo_filtro.set("Todas")

    def abrir_modal_nuevo(self):
        VentanaNuevoCurso(self, self.cargar_cursos)

    def cargar_cursos(self, *args):
        filtro_carrera = self.combo_filtro.get()
        termino_busqueda = self.ent_busqueda.get().strip()

        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        encabezados = ["Código", "Nombre", "Cupo", "Costo", "Carrera(s)", "Prelación", "Acciones"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_frame, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                # CORRECCIÓN: El JOIN de prelacion vuelve a ser pr.id_curso
                query = '''
                    SELECT c.id_curso, c.codigo, c.nombre, c.cupo_maximo, c.costo,
                           COALESCE(array_to_string(array_agg(DISTINCT ca.nombre), ', '), 'Asignación Pendiente') as carreras,
                           COALESCE(array_to_string(array_agg(DISTINCT cr.codigo), ', '), 'Ninguna') as prelaciones
                    FROM curso c
                    LEFT JOIN pensum p ON c.id_curso = p.id_curso
                    LEFT JOIN carrera ca ON p.id_carrera = ca.id_carrera
                    LEFT JOIN prelacion pr ON c.id_curso = pr.id_curso
                    LEFT JOIN curso cr ON pr.id_curso_requisito = cr.id_curso
                '''
                
                condiciones = []
                params = []

                if filtro_carrera != "Todas":
                    condiciones.append("c.id_curso IN (SELECT id_curso FROM pensum p2 JOIN carrera c2 ON p2.id_carrera = c2.id_carrera WHERE c2.nombre = %s)")
                    params.append(filtro_carrera)
                
                if termino_busqueda != "":
                    condiciones.append("(c.codigo ILIKE %s OR c.nombre ILIKE %s)")
                    params.extend([f"%{termino_busqueda}%", f"%{termino_busqueda}%"])

                if condiciones:
                    query += " WHERE " + " AND ".join(condiciones)

                query += " GROUP BY c.id_curso, c.codigo, c.nombre, c.cupo_maximo, c.costo ORDER BY c.codigo;"
                
                cur.execute(query, tuple(params))
                cursos = cur.fetchall()

                if not cursos:
                    ctk.CTkLabel(self.tabla_frame, text="No se encontraron cursos.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=7, pady=20)

                for fila_idx, est in enumerate(cursos, start=1):
                    id_curso, codigo, nombre, cupo, costo, carreras_str, prela_str = est

                    cod_str = codigo if codigo else "S/C" 
                    cupo_str = str(cupo) if cupo else "30"

                    ctk.CTkLabel(self.tabla_frame, text=cod_str, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=nombre, text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=cupo_str, text_color=TEXT_COLOR).grid(row=fila_idx, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=f"${costo:.2f}", text_color=TEXT_COLOR).grid(row=fila_idx, column=3, padx=5, pady=5, sticky="w")
                    
                    lbl_carrera = ctk.CTkLabel(self.tabla_frame, text=carreras_str, text_color=TEXT_COLOR, width=120, anchor="w")
                    lbl_carrera.grid(row=fila_idx, column=4, padx=5, pady=5, sticky="w")

                    lbl_prela = ctk.CTkLabel(self.tabla_frame, text=prela_str, text_color=TEXT_COLOR, width=100, anchor="w")
                    lbl_prela.grid(row=fila_idx, column=5, padx=5, pady=5, sticky="w")

                    frame_acciones = ctk.CTkFrame(self.tabla_frame, fg_color="transparent")
                    frame_acciones.grid(row=fila_idx, column=6, padx=5, pady=5, sticky="e")

                    btn_conf = ctk.CTkButton(frame_acciones, text="Configurar", width=70, fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=lambda i=id_curso: VentanaConfigurarCurso(self, i, self.cargar_cursos))
                    btn_conf.pack(side="left", padx=2)

                    btn_borrar = ctk.CTkButton(frame_acciones, text="X", width=30, fg_color=RED_COLOR, text_color=TEXT_COLOR, command=lambda i=id_curso: self.borrar_curso(i))
                    btn_borrar.pack(side="left", padx=2)

            except Exception as e:
                print("Error cargando cursos:", e)
            finally:
                cur.close()
                conn.close()

    def borrar_curso(self, id_curso):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("DELETE FROM curso WHERE id_curso = %s", (id_curso,))
                conn.commit()
                self.cargar_cursos()
            except Exception as e:
                conn.rollback()
                print(f"Error borrando curso: {e}")
            finally:
                cur.close()
                conn.close()