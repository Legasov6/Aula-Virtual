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
# VENTANA MODAL: NUEVA SECCIÓN
# ==========================================
class VentanaNuevaSeccion(ctk.CTkToplevel):
    def __init__(self, master, callback_actualizar):
        super().__init__(master)
        self.title("Abrir Nueva Sección")
        self.geometry("450x520")
        self.configure(fg_color=BG_COLOR)
        self.grab_set() 
        self.callback_actualizar = callback_actualizar

        self.id_periodo_activo = None

        ctk.CTkLabel(self, text="Apertura de Sección", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_COLOR).pack(pady=(15, 5))
        self.lbl_periodo = ctk.CTkLabel(self, text="Verificando periodo...", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR)
        self.lbl_periodo.pack(pady=(0, 10))

        ctk.CTkLabel(self, text="Materia:", text_color=TEXT_COLOR).pack(anchor="w", padx=75)
        self.combo_curso = ctk.CTkOptionMenu(self, width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR)
        self.combo_curso.pack(pady=(0, 10))

        ctk.CTkLabel(self, text="Buscar Profesor (Cédula o Nombre):", text_color=TEXT_COLOR).pack(anchor="w", padx=75)
        self.ent_buscar_prof = ctk.CTkEntry(self, placeholder_text="Escribe para filtrar...", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_buscar_prof.pack(pady=(0, 5))
        self.ent_buscar_prof.bind("<KeyRelease>", self.filtrar_profesores)

        ctk.CTkLabel(self, text="Profesor Asignado:", text_color=TEXT_COLOR).pack(anchor="w", padx=75)
        self.combo_profesor = ctk.CTkOptionMenu(self, width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR)
        self.combo_profesor.pack(pady=(0, 10))

        ctk.CTkLabel(self, text="Identificador de Sección (Ej: A, B, U1):", text_color=TEXT_COLOR).pack(anchor="w", padx=75)
        self.ent_identificador = ctk.CTkEntry(self, width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_identificador.pack(pady=(0, 10))

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=5)

        self.btn_guardar = ctk.CTkButton(self, text="Abrir Sección", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.guardar_bd)
        self.btn_guardar.pack(pady=10)

        self.mapa_cursos = {}
        self.mapa_profesores = {}
        self.lista_profesores_completa = [] 
        
        self.cargar_datos_formulario()

    def cargar_datos_formulario(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_periodo, codigo_periodo FROM periodo WHERE estado = 'Activo'")
                periodo = cur.fetchone()
                if not periodo:
                    self.lbl_periodo.configure(text="¡CRÍTICO: No hay periodo activo!", text_color=RED_COLOR)
                    self.lbl_error.configure(text="Ve a Institución y activa un periodo.")
                    self.btn_guardar.configure(state="disabled")
                    return
                
                self.id_periodo_activo = periodo[0]
                self.lbl_periodo.configure(text=f"Periodo Activo: {periodo[1]}")

                cur.execute("SELECT id_curso, codigo, nombre FROM curso ORDER BY nombre")
                for id_c, cod, nom in cur.fetchall():
                    texto = f"{cod} - {nom}" if cod else nom
                    self.mapa_cursos[texto] = id_c
                
                if self.mapa_cursos:
                    self.combo_curso.configure(values=list(self.mapa_cursos.keys()))
                    self.combo_curso.set(list(self.mapa_cursos.keys())[0])

                cur.execute("SELECT id_profesor, cedula, nombres, apellidos FROM profesor ORDER BY apellidos")
                for id_p, cedula, nom, ape in cur.fetchall():
                    texto = f"{ape}, {nom} ({cedula})" 
                    self.mapa_profesores[texto] = id_p
                    self.lista_profesores_completa.append(texto)
                
                if self.lista_profesores_completa:
                    self.combo_profesor.configure(values=self.lista_profesores_completa)
                    self.combo_profesor.set(self.lista_profesores_completa[0])

            except Exception as e:
                self.lbl_error.configure(text=f"Error cargando datos: {e}")
            finally:
                cur.close()
                conn.close()

    def filtrar_profesores(self, event=None):
        termino = self.ent_buscar_prof.get().strip().lower()
        if termino == "":
            opciones = self.lista_profesores_completa
        else:
            opciones = [p for p in self.lista_profesores_completa if termino in p.lower()]
        
        if opciones:
            self.combo_profesor.configure(values=opciones)
            self.combo_profesor.set(opciones[0])
        else:
            self.combo_profesor.configure(values=["No se encontraron coincidencias"])
            self.combo_profesor.set("No se encontraron coincidencias")

    def guardar_bd(self):
        if not self.id_periodo_activo: return

        curso_sel = self.combo_curso.get()
        prof_sel = self.combo_profesor.get()
        identificador = self.ent_identificador.get().strip().upper()

        if not curso_sel or prof_sel == "No se encontraron coincidencias" or not identificador:
            self.lbl_error.configure(text="Todos los campos son obligatorios.")
            return

        if prof_sel not in self.mapa_profesores or curso_sel not in self.mapa_cursos:
            self.lbl_error.configure(text="Seleccione un profesor y materia válidos.")
            return

        id_curso = self.mapa_cursos[curso_sel]
        id_profesor = self.mapa_profesores[prof_sel]

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute(
                    "INSERT INTO seccion (identificador, id_periodo, id_curso, id_profesor) VALUES (%s, %s, %s, %s)",
                    (identificador, self.id_periodo_activo, id_curso, id_profesor)
                )
                conn.commit()
                self.callback_actualizar()
                self.destroy()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                self.lbl_error.configure(text="Error: Ya existe esta sección en este periodo.")
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error inesperado: {e}")
            finally:
                cur.close()
                conn.close()

# ==========================================
# VENTANA MODAL: VER LISTA DE CLASE
# ==========================================
class VentanaListaClase(ctk.CTkToplevel):
    def __init__(self, master, id_seccion, nombre_clase):
        super().__init__(master)
        self.title(f"Lista de Clase: {nombre_clase}")
        self.geometry("500x500")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        ctk.CTkLabel(self, text=f"Inscritos en:\n{nombre_clase}", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_COLOR).pack(pady=15)

        self.tabla_alumnos = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_alumnos.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_alumnos.grid_columnconfigure((0,1,2), weight=1)

        self.cargar_alumnos(id_seccion)

    def cargar_alumnos(self, id_seccion):
        encabezados = ["Cédula", "Apellidos", "Nombres"]
        for i, txt in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_alumnos, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute('''
                    SELECT e.cedula, e.apellidos, e.nombres 
                    FROM inscripcion i
                    JOIN estudiante e ON i.id_estudiante = e.id_estudiante
                    WHERE i.id_seccion = %s
                    ORDER BY e.apellidos, e.nombres
                ''', (id_seccion,))
                
                alumnos = cur.fetchall()
                if not alumnos:
                    ctk.CTkLabel(self.tabla_alumnos, text="No hay alumnos inscritos aún.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=3, pady=20)
                
                for fila, (cedula, apellidos, nombres) in enumerate(alumnos, start=1):
                    ctk.CTkLabel(self.tabla_alumnos, text=cedula, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=2, sticky="w")
                    ctk.CTkLabel(self.tabla_alumnos, text=apellidos, text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=2, sticky="w")
                    ctk.CTkLabel(self.tabla_alumnos, text=nombres, text_color=TEXT_COLOR).grid(row=fila, column=2, padx=5, pady=2, sticky="w")
            except Exception as e:
                print("Error cargando lista:", e)
            finally:
                cur.close()
                conn.close()

# ==========================================
# VENTANA MODAL: GESTIONAR HORARIO
# ==========================================
class VentanaConfigurarHorario(ctk.CTkToplevel):
    def __init__(self, master, id_seccion, nombre_clase, callback_actualizar):
        super().__init__(master)
        self.title("Configurar Horario")
        self.geometry("500x550")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()
        
        self.id_seccion = id_seccion
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text=f"Horario: {nombre_clase}", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_COLOR).pack(pady=(15, 10))

        # Formulario de Nuevo Bloque de Horario
        frame_form = ctk.CTkFrame(self, fg_color="transparent")
        frame_form.pack(fill="x", padx=20)

        self.combo_dia = ctk.CTkOptionMenu(frame_form, values=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"], width=120, fg_color=SIDEBAR_COLOR, button_color=ACCENT_COLOR)
        self.combo_dia.grid(row=0, column=0, padx=5, pady=5)

        self.ent_inicio = ctk.CTkEntry(frame_form, placeholder_text="Inicio (HH:MM)", width=120, justify="center", fg_color=SIDEBAR_COLOR)
        self.ent_inicio.grid(row=0, column=1, padx=5, pady=5)

        self.ent_fin = ctk.CTkEntry(frame_form, placeholder_text="Fin (HH:MM)", width=120, justify="center", fg_color=SIDEBAR_COLOR)
        self.ent_fin.grid(row=0, column=2, padx=5, pady=5)

        btn_agregar = ctk.CTkButton(frame_form, text="+ Añadir", width=80, fg_color=GREEN_COLOR, text_color=BG_COLOR, command=self.agregar_horario)
        btn_agregar.grid(row=0, column=3, padx=5, pady=5)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=5)

        # Tabla de Horarios Actuales
        ctk.CTkFrame(self, height=2, fg_color=SIDEBAR_COLOR).pack(fill="x", padx=20, pady=5)
        
        self.tabla_horarios = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_horarios.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_horarios.grid_columnconfigure((0,1,2), weight=1)
        self.tabla_horarios.grid_columnconfigure(3, weight=0)

        self.cargar_horarios()

    def agregar_horario(self):
        dia = self.combo_dia.get()
        inicio = self.ent_inicio.get().strip()
        fin = self.ent_fin.get().strip()

        if not inicio or not fin:
            self.lbl_error.configure(text="Escribe la hora de inicio y fin.", text_color=RED_COLOR)
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("INSERT INTO horario (dia_semana, hora_inicio, hora_fin, id_seccion) VALUES (%s, %s, %s, %s)", 
                            (dia, inicio, fin, self.id_seccion))
                conn.commit()
                self.ent_inicio.delete(0, 'end')
                self.ent_fin.delete(0, 'end')
                self.lbl_error.configure(text="¡Bloque de horario añadido!", text_color=GREEN_COLOR)
                self.cargar_horarios()
                self.callback_actualizar() # Actualiza la tabla grande de secciones
            except psycopg2.errors.CheckViolation:
                conn.rollback()
                self.lbl_error.configure(text="La hora de Fin debe ser mayor a la de Inicio.", text_color=RED_COLOR)
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error de formato. Usa HH:MM (Ej: 14:30)", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()

    def cargar_horarios(self):
        for widget in self.tabla_horarios.winfo_children():
            widget.destroy()

        encabezados = ["Día", "Hora Inicio", "Hora Fin", "Acciones"]
        for i, txt in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_horarios, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                # Usamos substr para limpiar los segundos del formato time (08:00:00 -> 08:00)
                cur.execute('''
                    SELECT id_horario, dia_semana, substr(hora_inicio::text, 1, 5), substr(hora_fin::text, 1, 5) 
                    FROM horario WHERE id_seccion = %s ORDER BY id_horario
                ''', (self.id_seccion,))
                
                filas = cur.fetchall()
                if not filas:
                    ctk.CTkLabel(self.tabla_horarios, text="Sin horario asignado.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=4, pady=20)
                
                for fila, (id_h, dia, inicio, fin) in enumerate(filas, start=1):
                    ctk.CTkLabel(self.tabla_horarios, text=dia, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=2, sticky="w")
                    ctk.CTkLabel(self.tabla_horarios, text=inicio, text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=2, sticky="w")
                    ctk.CTkLabel(self.tabla_horarios, text=fin, text_color=TEXT_COLOR).grid(row=fila, column=2, padx=5, pady=2, sticky="w")
                    
                    btn_borrar = ctk.CTkButton(self.tabla_horarios, text="X", width=30, fg_color=RED_COLOR, text_color=TEXT_COLOR, command=lambda h=id_h: self.borrar_horario(h))
                    btn_borrar.grid(row=fila, column=3, padx=5, pady=2, sticky="e")
            except Exception as e:
                print("Error cargando horarios:", e)
            finally:
                cur.close()
                conn.close()

    def borrar_horario(self, id_horario):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("DELETE FROM horario WHERE id_horario = %s", (id_horario,))
                conn.commit()
                self.cargar_horarios()
                self.callback_actualizar()
            except Exception as e:
                conn.rollback()
                print("Error borrando:", e)
            finally:
                cur.close()
                conn.close()


# ==========================================
# PANEL PRINCIPAL: VISTA SECCIONES
# ==========================================
class VistaAdminSecciones(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_COLOR)
        
        self.titulo = ctk.CTkLabel(self, text="Gestión de Secciones", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.titulo.pack(pady=(20, 10))

        frame_controles = ctk.CTkFrame(self, fg_color="transparent")
        frame_controles.pack(fill="x", padx=20, pady=10)

        self.btn_listar = ctk.CTkButton(frame_controles, text="Recargar", width=90, fg_color=ACCENT_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.cargar_secciones)
        self.btn_listar.pack(side="left", padx=5)

        self.btn_nuevo = ctk.CTkButton(frame_controles, text="+ Nueva Sección", width=120, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=self.abrir_modal_nuevo)
        self.btn_nuevo.pack(side="left", padx=5)

        ctk.CTkLabel(frame_controles, text="Periodo:", text_color=TEXT_COLOR).pack(side="left", padx=(15, 2))
        self.combo_periodo = ctk.CTkOptionMenu(frame_controles, width=130, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.cargar_secciones)
        self.combo_periodo.pack(side="left", padx=5)

        # NUEVO FILTRO: Carrera
        ctk.CTkLabel(frame_controles, text="Carrera:", text_color=TEXT_COLOR).pack(side="left", padx=(10, 2))
        self.combo_carrera = ctk.CTkOptionMenu(frame_controles, width=150, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.cargar_secciones)
        self.combo_carrera.pack(side="left", padx=5)

        ctk.CTkLabel(frame_controles, text="Buscar:", text_color=TEXT_COLOR).pack(side="left", padx=(10, 2))
        self.ent_busqueda = ctk.CTkEntry(frame_controles, placeholder_text="Materia o Docente...", width=140, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_busqueda.pack(side="left", padx=5)
        self.ent_busqueda.bind("<Return>", lambda event: self.cargar_secciones())

        self.tabla_frame = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_frame.pack(padx=20, pady=10, fill="both", expand=True)
        # 5 Columnas en total ahora
        self.tabla_frame.grid_columnconfigure((0,1,2,3), weight=1)
        self.tabla_frame.grid_columnconfigure(4, weight=0)

        self.mapa_periodos = {}
        self.cargar_opciones_carreras()
        self.cargar_opciones_periodos()

    def cargar_opciones_carreras(self):
        conn, cur = conectar_bd()
        opciones = ["Todas"]
        if conn:
            try:
                cur.execute("SELECT nombre FROM carrera ORDER BY nombre;")
                opciones.extend([c[0] for c in cur.fetchall()])
            except Exception as e:
                print("Error cargando filtro de carreras:", e)
            finally:
                cur.close()
                conn.close()
        self.combo_carrera.configure(values=opciones)
        self.combo_carrera.set("Todas")

    def cargar_opciones_periodos(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_periodo, codigo_periodo, estado FROM periodo ORDER BY id_periodo DESC;")
                periodos = cur.fetchall()
                if periodos:
                    opciones = []
                    seleccion_por_defecto = None
                    for id_p, cod, est in periodos:
                        texto = f"{cod} (Activo)" if est == 'Activo' else cod
                        opciones.append(texto)
                        self.mapa_periodos[texto] = id_p
                        if est == 'Activo':
                            seleccion_por_defecto = texto
                    
                    self.combo_periodo.configure(values=opciones)
                    if seleccion_por_defecto:
                        self.combo_periodo.set(seleccion_por_defecto)
                    else:
                        self.combo_periodo.set(opciones[0])
                    self.cargar_secciones()
            except Exception as e:
                print("Error cargando filtro de periodos:", e)
            finally:
                cur.close()
                conn.close()

    def abrir_modal_nuevo(self):
        VentanaNuevaSeccion(self, self.cargar_secciones)

    def cargar_secciones(self, *args):
        seleccion_periodo = self.combo_periodo.get()
        if not seleccion_periodo or seleccion_periodo not in self.mapa_periodos: return
        id_periodo = self.mapa_periodos[seleccion_periodo]
        
        seleccion_carrera = self.combo_carrera.get()
        termino_busqueda = self.ent_busqueda.get().strip()

        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        # Quitamos "Materia" de las columnas porque ahora será un subtítulo agrupador
        encabezados = ["Sec.", "Profesor", "Horario", "Cupo (Ins/Max)", "Acciones"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_frame, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT s.id_seccion, s.identificador, c.nombre, p.nombres, p.apellidos, c.cupo_maximo,
                           (SELECT COUNT(*) FROM inscripcion i WHERE i.id_seccion = s.id_seccion) as inscritos,
                           COALESCE(array_to_string(array_agg(h.dia_semana || ' ' || substr(h.hora_inicio::text, 1, 5) || '-' || substr(h.hora_fin::text, 1, 5) ORDER BY h.id_horario), ' | '), 'Sin asignar') as horario_str
                    FROM seccion s
                    JOIN curso c ON s.id_curso = c.id_curso
                    JOIN profesor p ON s.id_profesor = p.id_profesor
                    LEFT JOIN horario h ON s.id_seccion = h.id_seccion
                    WHERE s.id_periodo = %s
                '''
                params = [id_periodo]

                # Filtro por Carrera
                if seleccion_carrera != "Todas":
                    query += " AND c.id_curso IN (SELECT id_curso FROM pensum p2 JOIN carrera c2 ON p2.id_carrera = c2.id_carrera WHERE c2.nombre = %s)"
                    params.append(seleccion_carrera)

                if termino_busqueda != "":
                    query += " AND (c.nombre ILIKE %s OR p.apellidos ILIKE %s)"
                    params.extend([f"%{termino_busqueda}%", f"%{termino_busqueda}%"])

                query += " GROUP BY s.id_seccion, c.nombre, p.nombres, p.apellidos, c.cupo_maximo ORDER BY c.nombre, s.identificador"
                
                cur.execute(query, tuple(params))
                secciones = cur.fetchall()

                if not secciones:
                    ctk.CTkLabel(self.tabla_frame, text="No hay secciones en este periodo.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=5, pady=20)

                fila_actual = 1
                curso_actual = None

                for id_sec, ident, curso, nom_prof, ape_prof, cupo_max, inscritos, horario_str in secciones:
                    # Lógica de agrupación visual
                    if curso != curso_actual:
                        curso_actual = curso
                        lbl_separador = ctk.CTkLabel(self.tabla_frame, text=f"--- {curso} ---", font=ctk.CTkFont(weight="bold", size=14), text_color=ACCENT_COLOR)
                        lbl_separador.grid(row=fila_actual, column=0, columnspan=5, pady=(15, 5), sticky="w")
                        fila_actual += 1

                    ctk.CTkLabel(self.tabla_frame, text=ident, text_color=TEXT_COLOR).grid(row=fila_actual, column=0, padx=15, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=f"{ape_prof}, {nom_prof}", text_color=TEXT_COLOR).grid(row=fila_actual, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=horario_str, text_color=TEXT_COLOR).grid(row=fila_actual, column=2, padx=5, pady=5, sticky="w")

                    color_cupo = RED_COLOR if inscritos >= cupo_max else TEXT_COLOR
                    ctk.CTkLabel(self.tabla_frame, text=f"{inscritos} / {cupo_max}", text_color=color_cupo, font=ctk.CTkFont(weight="bold")).grid(row=fila_actual, column=3, padx=5, pady=5, sticky="w")

                    frame_acciones = ctk.CTkFrame(self.tabla_frame, fg_color="transparent")
                    frame_acciones.grid(row=fila_actual, column=4, padx=5, pady=5, sticky="e")

                    btn_lista = ctk.CTkButton(frame_acciones, text="Ver Lista", width=70, fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=lambda id_s=id_sec, nom=f"{curso} ({ident})": VentanaListaClase(self, id_s, nom))
                    btn_lista.pack(side="left", padx=2)

                    btn_hora = ctk.CTkButton(frame_acciones, text="🕒 Horario", width=70, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=lambda id_s=id_sec, nom=f"{curso} ({ident})": VentanaConfigurarHorario(self, id_s, nom, self.cargar_secciones))
                    btn_hora.pack(side="left", padx=2)

                    btn_borrar = ctk.CTkButton(frame_acciones, text="X", width=30, fg_color=RED_COLOR, text_color=TEXT_COLOR, command=lambda id_s=id_sec: self.borrar_seccion(id_s))
                    btn_borrar.pack(side="left", padx=2)
                    
                    fila_actual += 1

            except Exception as e:
                print("Error cargando secciones:", e)
            finally:
                cur.close()
                conn.close()

    def borrar_seccion(self, id_seccion):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("DELETE FROM seccion WHERE id_seccion = %s", (id_seccion,))
                conn.commit()
                self.cargar_secciones()
            except Exception as e:
                conn.rollback()
                print(f"Error borrando sección: {e}")
            finally:
                cur.close()
                conn.close()