import tweepy
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from textwrap import wrap

def setup_twitter_client(bearer_token):
    """
    Configura y retorna el cliente de Twitter
    """
    try:
        client = tweepy.Client(bearer_token=bearer_token)
        print("✅ Cliente de Twitter configurado correctamente")
        return client
    except Exception as e:
        print(f"❌ Error al configurar el cliente: {e}")
        return None

def get_user_tweets_with_metrics(client, username, count=50):
    """
    Obtiene tweets con todas las métricas disponibles
    """
    try:
        # Obtener información del usuario
        user_response = client.get_user(
            username=username,
            user_fields=['public_metrics', 'description', 'created_at', 'verified']
        )
        
        if not user_response.data:
            print(f"❌ Usuario @{username} no encontrado")
            return None, None
        
        user = user_response.data
        user_id = user.id
        
        print(f"✅ Usuario encontrado: @{username}")
        print(f"📊 Seguidores: {user.public_metrics['followers_count']:,}")
        print(f"👥 Siguiendo: {user.public_metrics['following_count']:,}")
        print(f"📝 Tweets totales: {user.public_metrics['tweet_count']:,}")
        
        # Obtener tweets con métricas extendidas
        tweets_response = client.get_users_tweets(
            id=user_id,
            max_results=min(count, 100),  # Máximo 100 tweets por request
            tweet_fields=[
                'created_at', 
                'public_metrics',
                'context_annotations',
                'lang',
                'source'
            ],
            exclude=['retweets']  # Excluir retweets para ver contenido original
        )
        
        tweets = tweets_response.data if tweets_response.data else []
        print(f"📨 Se encontraron {len(tweets)} tweets")
        
        return user, tweets
        
    except tweepy.TooManyRequests:
        print("❌ Límite de la API alcanzado. Espera 15 minutos.")
        return None, None
    except Exception as e:
        print(f"❌ Error al obtener tweets: {e}")
        return None, None

def create_metrics_dataframe(tweets):
    """
    Crea un DataFrame con todas las métricas de los tweets
    """
    tweets_data = []
    
    for tweet in tweets:
        tweet_info = {
            'id': tweet.id,
            'fecha': tweet.created_at,
            'texto': tweet.text,
            'likes': tweet.public_metrics['like_count'],
            'retweets': tweet.public_metrics['retweet_count'],
            'respuestas': tweet.public_metrics['reply_count'],
            'vistas': tweet.public_metrics.get('impression_count', 0),  # Puede no estar disponible
            'citas': tweet.public_metrics.get('quote_count', 0),
            'idioma': getattr(tweet, 'lang', 'desconocido'),
            'fuente': getattr(tweet, 'source', 'desconocido')
        }
        tweets_data.append(tweet_info)
    
    df = pd.DataFrame(tweets_data)
    
    # Ordenar por fecha (más reciente primero)
    df = df.sort_values('fecha', ascending=False).reset_index(drop=True)
    
    return df

def display_detailed_metrics(df, username):
    """
    Muestra métricas detalladas y estadísticas
    """
    print(f"\n{'='*100}")
    print(f"📊 ANÁLISIS DETALLADO - @{username}")
    print(f"{'='*100}")
    
    # Estadísticas generales
    print(f"\n📈 ESTADÍSTICAS GENERALES (Últimos {len(df)} tweets):")
    print(f"❤️  Likes totales: {df['likes'].sum():,}")
    print(f"🔄 Retweets totales: {df['retweets'].sum():,}")
    print(f"💬 Respuestas totales: {df['respuestas'].sum():,}")
    print(f"👀 Vistas totales: {df['vistas'].sum():,}")
    print(f"📎 Citas totales: {df['citas'].sum():,}")
    
    print(f"\n📊 PROMEDIOS POR TWEET:")
    print(f"❤️  Likes promedio: {df['likes'].mean():.1f}")
    print(f"🔄 Retweets promedio: {df['retweets'].mean():.1f}")
    print(f"💬 Respuestas promedio: {df['respuestas'].mean():.1f}")
    print(f"👀 Vistas promedio: {df['vistas'].mean():.1f}")
    
    print(f"\n🏆 TWEETS MÁS POPULARES:")
    
    # Tweet con más likes
    max_likes = df.loc[df['likes'].idxmax()]
    print(f"\n❤️  MÁS LIKES ({max_likes['likes']:,}):")
    print(f"   Fecha: {max_likes['fecha'].strftime('%Y-%m-%d %H:%M')}")
    print(f"   Texto: {max_likes['texto'][:100]}...")
    
    # Tweet con más retweets
    max_rts = df.loc[df['retweets'].idxmax()]
    print(f"\n🔄 MÁS RETWEETS ({max_rts['retweets']:,}):")
    print(f"   Fecha: {max_rts['fecha'].strftime('%Y-%m-%d %H:%M')}")
    print(f"   Texto: {max_rts['texto'][:100]}...")
    
    # Tweet con más vistas
    if df['vistas'].sum() > 0:
        max_views = df.loc[df['vistas'].idxmax()]
        print(f"\n👀 MÁS VISTAS ({max_views['vistas']:,}):")
        print(f"   Fecha: {max_views['fecha'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Texto: {max_views['texto'][:100]}...")

def display_tweets_table(df):
    """
    Muestra una tabla con todos los tweets y sus métricas
    """
    print(f"\n{'='*150}")
    print(f"📋 DETALLE DE TWEETS (Últimos {len(df)} tweets)")
    print(f"{'='*150}")
    
    for idx, row in df.iterrows():
        tweet_num = idx + 1
        wrapped_text = '\n     '.join(wrap(row['texto'], width=80))
        
        print(f"\n#{tweet_num:02d} [{row['fecha'].strftime('%m/%d %H:%M')}]")
        print(f"   📝 {wrapped_text}")
        print(f"   📊 Métricas: ❤️ {row['likes']:>4} | 🔄 {row['retweets']:>3} | 💬 {row['respuestas']:>3} | 👀 {row['vistas']:>6} | 📎 {row['citas']:>2}")
        print(f"   🌐 Idioma: {row['idioma']} | 📱 Fuente: {row['fuente']}")

def save_analysis_to_excel(df, username, user_info):
    """
    Guarda el análisis completo en un archivo Excel
    """
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"analisis_twitter_{username}_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Hoja con todos los tweets
            df.to_excel(writer, sheet_name='Tweets Detallados', index=False)
            
            # Hoja con resumen estadístico
            summary_data = {
                'Métrica': ['Total Tweets Analizados', 'Periodo Analizado', 
                           'Likes Totales', 'Retweets Totales', 'Respuestas Totales',
                           'Vistas Totales', 'Citas Totales',
                           'Likes Promedio', 'Retweets Promedio', 'Respuestas Promedio',
                           'Vistas Promedio'],
                'Valor': [
                    len(df),
                    f"{df['fecha'].min().strftime('%Y-%m-%d')} a {df['fecha'].max().strftime('%Y-%m-%d')}",
                    df['likes'].sum(),
                    df['retweets'].sum(),
                    df['respuestas'].sum(),
                    df['vistas'].sum(),
                    df['citas'].sum(),
                    round(df['likes'].mean(), 1),
                    round(df['retweets'].mean(), 1),
                    round(df['respuestas'].mean(), 1),
                    round(df['vistas'].mean(), 1)
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja con top tweets
            top_likes = df.nlargest(5, 'likes')[['fecha', 'texto', 'likes', 'retweets', 'vistas']]
            top_retweets = df.nlargest(5, 'retweets')[['fecha', 'texto', 'likes', 'retweets', 'vistas']]
            
            top_likes.to_excel(writer, sheet_name='Top Likes', index=False)
            top_retweets.to_excel(writer, sheet_name='Top Retweets', index=False)
        
        print(f"\n💾 Análisis guardado en: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error al guardar el archivo Excel: {e}")
        return None

def plot_metrics(df, username):
    """
    Crea gráficos de las métricas (opcional)
    """
    try:
        # Configurar el estilo de los gráficos
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Análisis de Métricas - @{username}', fontsize=16, fontweight='bold')
        
        # Gráfico 1: Métricas por tweet (primeros 20 tweets para mejor visualización)
        df_plot = df.head(20).copy()
        df_plot['tweet_num'] = range(1, len(df_plot) + 1)
        
        axes[0, 0].plot(df_plot['tweet_num'], df_plot['likes'], marker='o', label='Likes', linewidth=2)
        axes[0, 0].plot(df_plot['tweet_num'], df_plot['retweets'], marker='s', label='Retweets', linewidth=2)
        axes[0, 0].plot(df_plot['tweet_num'], df_plot['respuestas'], marker='^', label='Respuestas', linewidth=2)
        axes[0, 0].set_title('Evolución de Métricas (Últimos 20 tweets)')
        axes[0, 0].set_xlabel('Número de Tweet')
        axes[0, 0].set_ylabel('Cantidad')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Gráfico 2: Distribución de likes
        axes[0, 1].hist(df['likes'], bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 1].set_title('Distribución de Likes')
        axes[0, 1].set_xlabel('Likes por Tweet')
        axes[0, 1].set_ylabel('Frecuencia')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Gráfico 3: Métricas totales
        metrics_sum = [df['likes'].sum(), df['retweets'].sum(), df['respuestas'].sum(), df['vistas'].sum()]
        metrics_labels = ['Likes', 'Retweets', 'Respuestas', 'Vistas']
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
        
        axes[1, 0].bar(metrics_labels, metrics_sum, color=colors, alpha=0.7)
        axes[1, 0].set_title('Métricas Totales Acumuladas')
        axes[1, 0].set_ylabel('Cantidad Total')
        for i, v in enumerate(metrics_sum):
            axes[1, 0].text(i, v, f'{v:,}', ha='center', va='bottom', fontweight='bold')
        
        # Gráfico 4: Correlación entre métricas
        correlation_data = df[['likes', 'retweets', 'respuestas', 'vistas']].corr()
        im = axes[1, 1].imshow(correlation_data, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        axes[1, 1].set_xticks(range(len(correlation_data.columns)))
        axes[1, 1].set_yticks(range(len(correlation_data.columns)))
        axes[1, 1].set_xticklabels(correlation_data.columns, rotation=45)
        axes[1, 1].set_yticklabels(correlation_data.columns)
        axes[1, 1].set_title('Matriz de Correlación')
        
        # Añadir valores de correlación
        for i in range(len(correlation_data.columns)):
            for j in range(len(correlation_data.columns)):
                axes[1, 1].text(j, i, f'{correlation_data.iloc[i, j]:.2f}', 
                               ha='center', va='center', color='white' if abs(correlation_data.iloc[i, j]) > 0.5 else 'black')
        
        plt.tight_layout()
        plt.savefig(f'metricas_{username}_{datetime.now().strftime("%Y%m%d_%H%M")}.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    except Exception as e:
        print(f"⚠️  No se pudieron generar los gráficos: {e}")

def main():
    """
    Función principal
    """
    print(" ANÁLISIS EGOCÉNTRICO")
    print("=" * 50)
    
    # Configurar tu Bearer Token aquí
    BEARER_TOKEN = "TU_BEARER_TOKEN_AQUÍ"
    
    if BEARER_TOKEN == "TU_BEARER_TOKEN_AQUÍ":
        print("❌ CONFIGURACIÓN REQUERIDA:")
        print("1. Ve a https://developer.twitter.com/")
        print("2. Crea una app y obtén el Bearer Token")
        print("3. Reemplaza 'TU_BEARER_TOKEN_AQUÍ' con tu token real")
        return
    
    # Configurar cliente
    client = setup_twitter_client(BEARER_TOKEN)
    if not client:
        return
    
    # Obtener username
    username = input("\nIngresa el nombre de usuario de Twitter (sin @): ").strip()
    if not username:
        print("❌ Debes ingresar un nombre de usuario válido")
        return
    
    # Obtener tweets y métricas
    print(f"\n📡 Obteniendo últimos 50 tweets de @{username}...")
    user_info, tweets = get_user_tweets_with_metrics(client, username, count=10)
    
    if not tweets:
        print("❌ No se pudieron obtener los tweets")
        return
    
    # Crear DataFrame con métricas
    df = create_metrics_dataframe(tweets)
    
    # Mostrar análisis
    display_detailed_metrics(df, username)
    display_tweets_table(df)
    
    # Guardar en Excel
    save_option = input("\n💾 ¿Deseas guardar el análisis en Excel? (s/n): ").lower()
    if save_option == 's':
        save_analysis_to_excel(df, username, user_info)
    
    # Generar gráficos
    plot_option = input("\n📊 ¿Deseas generar gráficos de las métricas? (s/n): ").lower()
    if plot_option == 's':
        plot_metrics(df, username)
    
    print(f"\n✅ Análisis completado para @{username}")

if __name__ == "__main__":
    main()

