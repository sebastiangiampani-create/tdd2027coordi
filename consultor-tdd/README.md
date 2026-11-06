# Consultor TDD 2027: versión de Work recuperada

Esta carpeta contiene los archivos originales de la versión 12 publicada en Work, commit `2c11e3a12ddfc11977b70577c88939ed5b4ed885`. No se reconstruyó a partir del consultor anterior de GitHub. `RECUPERACION.json` registra los hashes SHA-256 originales.

Se conserva el diseño, los filtros, el ordenamiento, las fuentes Google Sheets, los gráficos comparativos y la exportación XLSX con la hoja nominal `Docentes`. El único cambio funcional de presentación respecto del original es el estado **Con registro** solicitado para esta migración.

## Datos y conteo

La clave del cruce es escuela, área y turno. No exige comisión, QR ni fecha. Se incluyen registros sin convocatoria y se deduplica por DNI; el total global puede variar porque la fuente se consulta en vivo. No se fija artificialmente a 1.370. Las pruebas incluyen el caso de 1.370 DNI, con 1.291 coincidentes y 79 sin coincidencia.

El filtro de dependencia usa la dependencia funcional registrada y, para escuelas sin asistentes, la clasificación disponible por institución. La tabla, los gráficos y las exportaciones se calculan sobre los mismos resultados filtrados. El archivo Excel contiene `Resumen`, `Docentes`, `Filtros` y los datos de ambos gráficos. La hoja `Docentes` conserva la granularidad del original: un DNI por escuela/área/turno; un mismo DNI puede aparecer en distintos contextos.

Los previstos docentes de referencia son DEM 2.045, DET 1.393, DENS 113 y DEA 302: total 3.853. Se utilizan solo cuando el desglose permite aplicar los filtros. Los enlaces de convocatoria no contienen previstos docentes por escuela; se conserva la carga opcional de esos datos y el estado «Sin dato» cuando falta denominador.

## Integración y validación

El portal agrega un acceso independiente a `consultor-tdd-2027.html`. Ese HTML conserva el contenido original y utiliza los recursos de `consultor-tdd/assets/`. Se conservan íntegros `consultor-informes.html`, todos los accesos anteriores del portal y el sitio original de Work. La carpeta `consultor-tdd/` también conserva la entrada original recuperada.

Pruebas: `node --test tests/consultor-tdd.test.cjs`. Incluyen procedencia del código, DNI únicos, registros sin convocatoria, filtros combinados, gráficos y lectura del XLSX generado por el código original.
