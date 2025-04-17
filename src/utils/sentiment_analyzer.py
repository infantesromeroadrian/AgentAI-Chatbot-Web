"""
Módulo para análisis de sentimiento en mensajes de usuario.
Proporciona funcionalidades para detectar emociones y estados de ánimo
en los mensajes, permitiendo respuestas más contextuales.
"""
import re
from typing import Dict, List, Tuple, Any, Optional
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analizador de sentimiento para mensajes en español.
    Utiliza un enfoque basado en reglas y léxico para detectar
    emociones básicas y polaridad del texto.
    """
    
    def __init__(self):
        """
        Inicializa el analizador de sentimiento con diccionarios de palabras
        y patrones para detección de emociones.
        """
        # Diccionarios de palabras de emoción (simplificado)
        self.emotion_lexicon = {
            'alegria': [
                'feliz', 'contento', 'encantado', 'satisfecho', 'maravilloso', 
                'excelente', 'genial', 'fantástico', 'alegre', 'entusiasmado',
                'gustar', 'encantar', 'amar', 'perfecto', 'gracias'
            ],
            'tristeza': [
                'triste', 'decepcionado', 'desanimado', 'infeliz', 'pena',
                'melancolía', 'melancolico', 'lástima', 'lastima', 'desilusión',
                'desilusionado', 'mal', 'horrible', 'terrible', 'peor'
            ],
            'enojo': [
                'enojado', 'enfadado', 'molesto', 'irritado', 'furioso', 'rabia',
                'indignado', 'frustrado', 'harto', 'abandonar', 'inútil', 'ineficiente',
                'incompetente', 'absurdo', 'ridículo', 'estúpido'
            ],
            'miedo': [
                'asustado', 'preocupado', 'nervioso', 'inseguro', 'temeroso',
                'alarmado', 'ansiedad', 'pánico', 'panico', 'terror', 'inquieto',
                'intranquilo', 'miedo', 'temor', 'incertidumbre'
            ],
            'sorpresa': [
                'sorprendido', 'asombrado', 'impresionado', 'perplejo', 'impactado',
                'increíble', 'increible', 'inesperado', 'extraordinario', 'impresionante',
                'inusual', 'raro', 'extraño', 'wow', 'dios mío'
            ],
            'confusión': [
                'confundido', 'perdido', 'desorientado', 'complicado', 'complejo',
                'confuso', 'lío', 'desorden', 'caos', 'no entiendo', 'difícil',
                'difícil de entender', 'qué', 'cómo', 'por qué', 'no comprendo'
            ]
        }
        
        # Patrones para intensificadores y negaciones
        self.intensifiers = [
            'muy', 'extremadamente', 'absolutamente', 'completamente', 'totalmente',
            'bastante', 'demasiado', 'super', 'realmente', 'verdaderamente'
        ]
        
        self.negations = [
            'no', 'ni', 'nunca', 'jamás', 'tampoco', 'ningún', 'ninguno', 'nada'
        ]
        
        # Patrones de polaridad
        self.positive_patterns = [
            r'\b(me gusta|excelente|perfecto|bien|bueno|genial|gracias)\b',
            r'(:\)|😊|😄|👍|❤️|♥|👏)'
        ]
        
        self.negative_patterns = [
            r'\b(no funciona|error|problema|falla|malo|pésimo|terrible)\b',
            r'(:\(|😞|😢|👎|😠|😡|🤬)'
        ]
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analiza el sentimiento del texto proporcionado.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con análisis de sentimiento
        """
        # Normalizar texto
        normalized_text = text.lower()
        
        # Detectar emociones
        emotions = self._detect_emotions(normalized_text)
        
        # Analizar polaridad
        polarity = self._analyze_polarity(normalized_text)
        
        # Detectar urgencia
        urgency = self._detect_urgency(normalized_text)
        
        # Componer resultado
        result = {
            'polarity': polarity,
            'emotions': emotions,
            'dominant_emotion': self._get_dominant_emotion(emotions),
            'urgency': urgency,
            'confidence': self._calculate_confidence(emotions, polarity)
        }
        
        logger.debug(f"Análisis de sentimiento: {result}")
        return result
    
    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """
        Detecta emociones en el texto basado en palabras clave.
        
        Args:
            text: Texto normalizado a analizar
            
        Returns:
            Diccionario con puntuaciones para cada emoción
        """
        emotions = {emotion: 0.0 for emotion in self.emotion_lexicon.keys()}
        words = re.findall(r'\b\w+\b', text)
        
        # Detectar negaciones en el texto
        negation_indices = [i for i, word in enumerate(words) 
                          if word in self.negations]
        
        for emotion, keywords in self.emotion_lexicon.items():
            for keyword in keywords:
                # Buscar la palabra clave en el texto
                if keyword in text:
                    # Obtener todas las ocurrencias
                    for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', text):
                        start = match.start()
                        
                        # Calcular el índice aproximado en la lista de palabras
                        word_index = len(text[:start].split()) - 1
                        
                        # Verificar si hay una negación cercana (hasta 3 palabras antes)
                        is_negated = any(neg_idx >= 0 and neg_idx < word_index and 
                                         word_index - neg_idx <= 3 
                                         for neg_idx in negation_indices)
                        
                        # Calcular puntuación
                        if is_negated:
                            # Si hay negación, invertir la emoción o reducir su intensidad
                            opposite_emotion = self._get_opposite_emotion(emotion)
                            if opposite_emotion:
                                emotions[opposite_emotion] += 0.5
                            else:
                                emotions[emotion] -= 0.3  # Reducir si no hay opuesto
                        else:
                            # Sin negación, añadir puntuación normal
                            emotions[emotion] += 1.0
                            
                            # Verificar intensificadores
                            for intensifier in self.intensifiers:
                                pattern = r'\b' + re.escape(intensifier) + r'\s+' + re.escape(keyword)
                                if re.search(pattern, text):
                                    emotions[emotion] += 0.5
        
        # Normalizar puntuaciones (0.0 - 1.0)
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: min(v/max(total, 1.0), 1.0) for k, v in emotions.items()}
        
        return emotions
    
    def _analyze_polarity(self, text: str) -> float:
        """
        Determina la polaridad del texto (positivo o negativo).
        
        Args:
            text: Texto normalizado a analizar
            
        Returns:
            Puntuación de polaridad entre -1.0 (negativo) y 1.0 (positivo)
        """
        # Inicializar puntuación
        score = 0.0
        
        # Comprobar patrones positivos
        positive_count = 0
        for pattern in self.positive_patterns:
            matches = re.findall(pattern, text)
            positive_count += len(matches)
            score += len(matches) * 0.5
        
        # Comprobar patrones negativos
        negative_count = 0
        for pattern in self.negative_patterns:
            matches = re.findall(pattern, text)
            negative_count += len(matches)
            score -= len(matches) * 0.5
        
        # Normalizar entre -1 y 1
        if positive_count + negative_count > 0:
            score = max(min(score, 1.0), -1.0)
        
        return score
    
    def _detect_urgency(self, text: str) -> float:
        """
        Detecta el nivel de urgencia en el mensaje.
        
        Args:
            text: Texto normalizado a analizar
            
        Returns:
            Nivel de urgencia entre 0.0 (baja) y 1.0 (alta)
        """
        urgency_score = 0.0
        
        # Palabras que indican urgencia
        urgency_words = [
            'urgente', 'inmediato', 'rápido', 'prisa', 'ahora', 'emergencia',
            'crítico', 'crítica', 'grave', 'importante', 'pronto', 'ya'
        ]
        
        # Patrones de urgencia (signos de exclamación, mayúsculas, repetición)
        urgency_patterns = [
            (r'!{2,}', 0.3),  # Múltiples signos de exclamación
            (r'\?{2,}', 0.2),  # Múltiples signos de interrogación
            (r'[A-ZÁÉÍÓÚÑ]{3,}', 0.2)  # Palabras en mayúsculas (3+ letras)
        ]
        
        # Verificar palabras de urgencia
        for word in urgency_words:
            if word in text:
                urgency_score += 0.2
                
                # Si está combinada con intensificadores, aumentar aún más
                for intensifier in self.intensifiers:
                    if intensifier + ' ' + word in text:
                        urgency_score += 0.1
        
        # Verificar patrones de urgencia
        for pattern, score in urgency_patterns:
            if re.search(pattern, text):
                urgency_score += score
        
        # Limitar a 1.0
        return min(urgency_score, 1.0)
    
    def _get_dominant_emotion(self, emotions: Dict[str, float]) -> Optional[str]:
        """
        Obtiene la emoción dominante del análisis.
        
        Args:
            emotions: Diccionario con puntuaciones de emociones
            
        Returns:
            Nombre de la emoción dominante o None si no hay ninguna
        """
        if not emotions:
            return None
            
        # Filtrar emociones con puntuación mínima
        valid_emotions = {k: v for k, v in emotions.items() if v >= 0.2}
        
        if not valid_emotions:
            return None
            
        # Obtener la emoción con mayor puntuación
        return max(valid_emotions.items(), key=lambda x: x[1])[0]
    
    def _get_opposite_emotion(self, emotion: str) -> Optional[str]:
        """
        Obtiene la emoción opuesta a la dada.
        
        Args:
            emotion: Nombre de la emoción
            
        Returns:
            Nombre de la emoción opuesta o None si no hay un opuesto claro
        """
        opposites = {
            'alegria': 'tristeza',
            'tristeza': 'alegria',
            'enojo': 'alegria',
            'miedo': 'alegria',
            'confusión': 'alegria'
        }
        
        return opposites.get(emotion)
    
    def _calculate_confidence(self, emotions: Dict[str, float], polarity: float) -> float:
        """
        Calcula la confianza del análisis basado en la claridad de las emociones y polaridad.
        
        Args:
            emotions: Diccionario con puntuaciones de emociones
            polarity: Puntuación de polaridad
            
        Returns:
            Nivel de confianza entre 0.0 y 1.0
        """
        # Si hay una emoción claramente dominante, mayor confianza
        emotion_values = list(emotions.values())
        if emotion_values:
            emotion_values.sort(reverse=True)
            if len(emotion_values) >= 2:
                # Diferencia entre la emoción principal y la segunda
                emotion_clarity = emotion_values[0] - emotion_values[1]
            else:
                emotion_clarity = emotion_values[0]
        else:
            emotion_clarity = 0.0
        
        # La polaridad fuerte también aumenta la confianza
        polarity_strength = abs(polarity)
        
        # Combinar factores para obtener confianza final
        confidence = (emotion_clarity * 0.6) + (polarity_strength * 0.4)
        
        return min(confidence, 1.0)
    
    def get_response_suggestion(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera sugerencias de respuesta basadas en el análisis de sentimiento.
        
        Args:
            analysis: Resultado del análisis de sentimiento
            
        Returns:
            Diccionario con sugerencias para la respuesta
        """
        suggestions = {
            'tone': 'neutral',  # tono sugerido: empático, formal, alegre, etc.
            'priority': 'normal',  # prioridad: alta, normal, baja
            'focus': []  # aspectos a enfatizar en la respuesta
        }
        
        # Determinar tono basado en emociones dominantes y polaridad
        dominant_emotion = analysis.get('dominant_emotion')
        polarity = analysis.get('polarity', 0)
        
        # Definir tono según emoción y polaridad
        if dominant_emotion == 'alegria' or polarity > 0.5:
            suggestions['tone'] = 'alegre'
        elif dominant_emotion == 'tristeza' or polarity < -0.3:
            suggestions['tone'] = 'empático'
        elif dominant_emotion == 'enojo' and polarity < -0.2:
            suggestions['tone'] = 'calmado'
        elif dominant_emotion == 'miedo' or dominant_emotion == 'confusión':
            suggestions['tone'] = 'tranquilizador'
        elif dominant_emotion == 'sorpresa':
            suggestions['tone'] = 'informativo'
        
        # Determinar prioridad basada en urgencia
        urgency = analysis.get('urgency', 0)
        if urgency > 0.7:
            suggestions['priority'] = 'alta'
        elif urgency > 0.3:
            suggestions['priority'] = 'media'
        
        # Aspectos a enfatizar
        if dominant_emotion == 'confusión':
            suggestions['focus'].append('claridad')
        if dominant_emotion == 'miedo':
            suggestions['focus'].append('seguridad')
        if polarity < -0.5:
            suggestions['focus'].append('solución')
        if dominant_emotion == 'enojo':
            suggestions['focus'].append('disculpa')
        
        return suggestions 