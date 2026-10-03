import customtkinter as ctk
import psycopg2
import csv
from tkinter import filedialog, messagebox
from conexion import conectar_bd

BG_COLOR = "#282828"
SIDEBAR_COLOR = "#3c3836"
ACCENT_COLOR = "#d79921"
TEXT_COLOR = "#ebdbb2"
GREEN_COLOR = "#98971a"
BLUE_COLOR = "#458588"
RED_COLOR = "#cc241d" 

class VistaAdminReportes(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_COLOR)
        
        ctk.CTkLabel(self, text="Panel de Reportes y Estadísticas", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR).pack(pady=(20, 10))

        self.tabview = ctk.CTkTabview(self, fg_color=SIDEBAR_COLOR, segmented_button_selected_color=ACCENT_COLOR, segmented_button_selected_hover_color="#b57614")
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_finanzas = self.tabview.add("Ingresos Financieros")
        self.tab_poblacion = self.tabview.add("Población Estudiantil")
        self.tab_rendimiento = self.tabview.add("Rendimiento Académico")
        self.tab_demanda = self.tabview.add("Demanda y Espera")   # <--- NUEVO
        self.tab_carga = self.tabview.add("Carga Docente")        # <--- NUEVO

        self.construir_reporte_finanzas()
        self.construir_reporte_poblacion()
        self.construir_reporte_rendimiento()
        self.construir_reporte_demanda()   # <--- NUEVO
        self.construir_reporte_carga()     # <--- NUEVO

    # --- REPORTE 1: INGRESOS POR PERIODO ---
    def construir_reporte_finanzas(self):
        btn_exportar = ctk.CTkButton(self.tab_finanzas, text="📥 Exportar a CSV", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=lambda: self.exportar_csv(self.datos_finanzas, self.encabezados_finanzas, "Reporte_Financiero"))
        btn_exportar.pack(pady=10, anchor="e", padx=20)

        self.tabla_finanzas = ctk.CTkScrollableFrame(self.tab_finanzas, fg_color=BG_COLOR)
        self.tabla_finanzas.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_finanzas.grid_columnconfigure((0,1,2), weight=1)

        self.encabezados_finanzas = ["Código Periodo", "Inscripciones Procesadas", "Total Recaudado ($)"]
        self.datos_finanzas = []
        self.cargar_finanzas()

    def cargar_finanzas(self):
        for i, txt in enumerate(self.encabezados_finanzas):
            ctk.CTkLabel(self.tabla_finanzas, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT p.codigo_periodo, 
                           COUNT(i.id_inscripcion), 
                           COALESCE(SUM(i.costo_cobrado), 0)
                    FROM periodo p
                    LEFT JOIN seccion s ON p.id_periodo = s.id_periodo
                    LEFT JOIN inscripcion i ON s.id_seccion = i.id_seccion AND i.estado = 'Inscrito'
                    GROUP BY p.codigo_periodo
                    ORDER BY p.codigo_periodo DESC
                '''
                cur.execute(query)
                self.datos_finanzas = cur.fetchall()

                for fila, (periodo, conteo, total) in enumerate(self.datos_finanzas, start=1):
                    ctk.CTkLabel(self.tabla_finanzas, text=periodo, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_finanzas, text=str(conteo), text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_finanzas, text=f"${total:,.2f}", text_color=GREEN_COLOR, font=ctk.CTkFont(weight="bold")).grid(row=fila, column=2, padx=5, pady=5, sticky="w")
            finally:
                cur.close()
                conn.close()

    # --- REPORTE 2: POBLACIÓN POR CARRERA ---
    def construir_reporte_poblacion(self):
        btn_exportar = ctk.CTkButton(self.tab_poblacion, text="📥 Exportar a CSV", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=lambda: self.exportar_csv(self.datos_poblacion, self.encabezados_poblacion, "Reporte_Poblacion"))
        btn_exportar.pack(pady=10, anchor="e", padx=20)

        self.tabla_pob = ctk.CTkScrollableFrame(self.tab_poblacion, fg_color=BG_COLOR)
        self.tabla_pob.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_pob.grid_columnconfigure((0,1), weight=1)

        self.encabezados_poblacion = ["Carrera", "Estudiantes Activos"]
        self.datos_poblacion = []
        self.cargar_poblacion()

    def cargar_poblacion(self):
        for i, txt in enumerate(self.encabezados_poblacion):
            ctk.CTkLabel(self.tabla_pob, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT c.nombre, COUNT(ec.id_estudiante)
                    FROM carrera c
                    LEFT JOIN expediente_carrera ec ON c.id_carrera = ec.id_carrera AND ec.estado = 'Activo'
                    GROUP BY c.nombre
                    ORDER BY COUNT(ec.id_estudiante) DESC
                '''
                cur.execute(query)
                self.datos_poblacion = cur.fetchall()

                for fila, (carrera, cantidad) in enumerate(self.datos_poblacion, start=1):
                    ctk.CTkLabel(self.tabla_pob, text=carrera, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_pob, text=str(cantidad), text_color=TEXT_COLOR, font=ctk.CTkFont(weight="bold")).grid(row=fila, column=1, padx=5, pady=5, sticky="w")
            finally:
                cur.close()
                conn.close()

    # --- REPORTE 3: RENDIMIENTO ACADÉMICO ---
    def construir_reporte_rendimiento(self):
        btn_exportar = ctk.CTkButton(self.tab_rendimiento, text="📥 Exportar a CSV", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=lambda: self.exportar_csv(self.datos_rendimiento, self.encabezados_rendimiento, "Reporte_Rendimiento"))
        btn_exportar.pack(pady=10, anchor="e", padx=20)

        self.tabla_ren = ctk.CTkScrollableFrame(self.tab_rendimiento, fg_color=BG_COLOR)
        self.tabla_ren.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_ren.grid_columnconfigure((0,1,2,3), weight=1)

        self.encabezados_rendimiento = ["Materia", "Evaluaciones Aplicadas", "Aprobados", "Reprobados"]
        self.datos_rendimiento = []
        self.cargar_rendimiento()

    def cargar_rendimiento(self):
        for i, txt in enumerate(self.encabezados_rendimiento):
            ctk.CTkLabel(self.tabla_ren, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                # Contamos calificaciones globales por materia
                query = '''
                    SELECT cu.nombre,
                           COUNT(c.id_calificacion),
                           COUNT(c.id_calificacion) FILTER (WHERE c.nota_conceptual = 'Aprobado'),
                           COUNT(c.id_calificacion) FILTER (WHERE c.nota_conceptual = 'Reprobado')
                    FROM curso cu
                    LEFT JOIN seccion s ON cu.id_curso = s.id_curso
                    LEFT JOIN evaluacion e ON s.id_seccion = e.id_seccion
                    LEFT JOIN calificacion c ON e.id_evaluacion = c.id_evaluacion
                    GROUP BY cu.nombre
                    ORDER BY cu.nombre
                '''
                cur.execute(query)
                self.datos_rendimiento = cur.fetchall()

                for fila, (materia, total, aprob, reprob) in enumerate(self.datos_rendimiento, start=1):
                    ctk.CTkLabel(self.tabla_ren, text=materia, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_ren, text=str(total), text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_ren, text=str(aprob), text_color=BLUE_COLOR, font=ctk.CTkFont(weight="bold")).grid(row=fila, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_ren, text=str(reprob), text_color=RED_COLOR, font=ctk.CTkFont(weight="bold")).grid(row=fila, column=3, padx=5, pady=5, sticky="w")
            finally:
                cur.close()
                conn.close()

# --- REPORTE 4: DEMANDA Y LISTAS DE ESPERA (PERIODO ACTIVO) ---
    def construir_reporte_demanda(self):
        btn_exportar = ctk.CTkButton(self.tab_demanda, text="📥 Exportar a CSV", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=lambda: self.exportar_csv(self.datos_demanda, self.encabezados_demanda, "Reporte_Demanda_Materias"))
        btn_exportar.pack(pady=10, anchor="e", padx=20)

        self.tabla_demanda = ctk.CTkScrollableFrame(self.tab_demanda, fg_color=BG_COLOR)
        self.tabla_demanda.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_demanda.grid_columnconfigure((0,1,2,3), weight=1)

        self.encabezados_demanda = ["Materia", "Secciones Abiertas", "Inscritos (Activos)", "En Lista de Espera"]
        self.datos_demanda = []
        self.cargar_demanda()

    def cargar_demanda(self):
        for i, txt in enumerate(self.encabezados_demanda):
            ctk.CTkLabel(self.tabla_demanda, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                # Usamos FILTER de PostgreSQL para separar inscritos de lista de espera
                query = '''
                    SELECT c.nombre, 
                           COUNT(DISTINCT s.id_seccion),
                           COUNT(i.id_inscripcion) FILTER (WHERE i.estado = 'Inscrito'),
                           COUNT(i.id_inscripcion) FILTER (WHERE i.estado = 'En_espera')
                    FROM curso c
                    JOIN seccion s ON c.id_curso = s.id_curso
                    JOIN periodo p ON s.id_periodo = p.id_periodo AND p.estado = 'Activo'
                    LEFT JOIN inscripcion i ON s.id_seccion = i.id_seccion
                    GROUP BY c.nombre
                    ORDER BY COUNT(i.id_inscripcion) FILTER (WHERE i.estado = 'En_espera') DESC, 
                             COUNT(i.id_inscripcion) FILTER (WHERE i.estado = 'Inscrito') DESC
                '''
                cur.execute(query)
                self.datos_demanda = cur.fetchall()

                for fila, (materia, secs, inscritos, espera) in enumerate(self.datos_demanda, start=1):
                    # Si hay gente en espera, lo pintamos de rojo para llamar la atención del admin
                    color_espera = RED_COLOR if espera and espera > 0 else TEXT_COLOR
                    str_espera = f"⚠️ {espera}" if espera and espera > 0 else "0"
                    
                    # Convertimos None a 0 de forma segura para la interfaz
                    secs = secs if secs else 0
                    inscritos = inscritos if inscritos else 0

                    ctk.CTkLabel(self.tabla_demanda, text=materia, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_demanda, text=str(secs), text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_demanda, text=str(inscritos), text_color=BLUE_COLOR, font=ctk.CTkFont(weight="bold")).grid(row=fila, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_demanda, text=str_espera, text_color=color_espera, font=ctk.CTkFont(weight="bold")).grid(row=fila, column=3, padx=5, pady=5, sticky="w")
            finally:
                cur.close()
                conn.close()

    # --- REPORTE 5: CARGA DOCENTE (PERIODO ACTIVO) ---
    def construir_reporte_carga(self):
        btn_exportar = ctk.CTkButton(self.tab_carga, text="📥 Exportar a CSV", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=lambda: self.exportar_csv(self.datos_carga, self.encabezados_carga, "Reporte_Carga_Docente"))
        btn_exportar.pack(pady=10, anchor="e", padx=20)

        self.tabla_carga = ctk.CTkScrollableFrame(self.tab_carga, fg_color=BG_COLOR)
        self.tabla_carga.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_carga.grid_columnconfigure((0,1,2), weight=1)

        self.encabezados_carga = ["Profesor", "Secciones Asignadas", "Total Alumnos a Cargo"]
        self.datos_carga = []
        self.cargar_carga_docente()

    def cargar_carga_docente(self):
        for i, txt in enumerate(self.encabezados_carga):
            ctk.CTkLabel(self.tabla_carga, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT p.apellidos || ', ' || p.nombres,
                           COUNT(DISTINCT s.id_seccion),
                           COUNT(i.id_inscripcion) FILTER (WHERE i.estado = 'Inscrito')
                    FROM profesor p
                    JOIN seccion s ON p.id_profesor = s.id_profesor
                    JOIN periodo per ON s.id_periodo = per.id_periodo AND per.estado = 'Activo'
                    LEFT JOIN inscripcion i ON s.id_seccion = i.id_seccion
                    GROUP BY p.id_profesor, p.apellidos, p.nombres
                    ORDER BY COUNT(i.id_inscripcion) FILTER (WHERE i.estado = 'Inscrito') DESC
                '''
                cur.execute(query)
                self.datos_carga = cur.fetchall()

                for fila, (profesor, secciones, alumnos) in enumerate(self.datos_carga, start=1):
                    # Convertimos None a 0
                    secciones = secciones if secciones else 0
                    alumnos = alumnos if alumnos else 0

                    ctk.CTkLabel(self.tabla_carga, text=profesor, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_carga, text=str(secciones), text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_carga, text=str(alumnos), text_color=ACCENT_COLOR, font=ctk.CTkFont(weight="bold")).grid(row=fila, column=2, padx=5, pady=5, sticky="w")
            finally:
                cur.close()
                conn.close()
    # --- MOTOR DE EXPORTACIÓN ---
    def exportar_csv(self, datos, encabezados, nombre_sugerido):
        if not datos:
            messagebox.showwarning("Sin Datos", "No hay datos para exportar en este reporte.")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=nombre_sugerido,
            title="Guardar Reporte Como",
            filetypes=[("Archivos CSV", "*.csv")]
        )

        if archivo:
            try:
                # encoding='utf-8-sig' asegura que Excel lea las tildes y ñ correctamente
                with open(archivo, mode='w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow(encabezados)
                    for fila in datos:
                        writer.writerow(fila)
                messagebox.showinfo("Éxito", f"Reporte exportado correctamente a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")