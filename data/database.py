def salvar_no_postgres(df, nome_tabela):
    print(f"Iniciando gravação na tabela '{nome_tabela}'...")

    db_url = "jdbc:postgresql://localhost:5432/projeto_zarc"

    try:
        (
            df.write
            .format("jdbc")
            .option("url", db_url)
            .option("dbtable", nome_tabela)
            .option("user", "teste")
            .option("password", "1234")
            .option("driver", "org.postgresql.Driver")

            # 🔥 Apenas o batchsize é útil aqui para desempenho na GRAVAÇÃO
            .option("batchsize", "30000") 
            
            # 🔥 Estabilidade
            .option("socketTimeout", "300000")
            .option("loginTimeout", "30")

            .mode("overwrite")
            .save()
        )

        print(f"Sucesso! Dados gravados na tabela '{nome_tabela}'.")

    except Exception:
        import traceback
        traceback.print_exc()