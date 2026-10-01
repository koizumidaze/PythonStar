import re
import random
import time
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable

PRONOUN_SWAP = {
    "i": "you", "you": "i",
    "me": "you",
    "my": "your",
    "am": "are", "are": "am", "was": "were",
    "i'd": "you would", "i've": "you have", "i'll": "you will",
    "yours": "mine", "mine": "yours",
    "myself": "yourself", "yourself": "myself",
    "we": "you", "us": "you", "our": "your", "ours": "yours",
    "they": "you", "them": "you", "their": "your", "theirs": "yours",
    "himself": "yourself", "herself": "yourself", "themselves": "yourself",
}


def user_to_bot(text: str) -> str:
    if re.search(r'[a-zA-Z]', text):
        words = text.split()
        swapped = [PRONOUN_SWAP.get(w.lower(), w) for w in words]
        return " ".join(swapped)
    else:
        replacements = [("my", "your"), ("me", "you"), ("myself", "yourself")]
        for old, new in replacements:
            text = text.replace(old, new)
        return text


def swap_pronouns(phrase: str) -> str:
    words = phrase.lower().split()
    swapped_words = [PRONOUN_SWAP.get(word, word) for word in words]
    return " ".join(swapped_words)


rules = {
    # ---------- Greetings & small talk (must come first) ----------
    r'^(hello|hi|hey|hiya|yo|howdy)\b.*': [
        "Hello! I'm glad you're here. How are you feeling today?",
        "Hi there. It's good to see you. What's on your mind today?",
        "Hey. I'm here and ready to listen. How has your day been so far?"
    ],
    r'^(hello|hi|hey)\s+(star|there)\b.*': [
        "Hello! Yes, I'm Star. It's nice to meet you. What would you like to talk about today?",
        "Hi, I'm Star. I'm here for you. How are you doing right now?",
        "Hey there. Star here, ready to listen. What's been going on with you?"
    ],
    r'^good\s+(morning|afternoon|evening)\b.*': [
        "Good {0} to you too. How are you feeling this {0}?",
        "Good {0}. I hope you're doing okay. What's on your mind today?",
        "Good {0}. I'm here whenever you're ready to talk. How are things with you?"
    ],
    r'^how are you(.*)\?*$': [
        "Thank you for asking. I'm here and fully focused on you. How are you really doing today?",
        "I appreciate you asking. I'm here to listen. How are you feeling right now?",
        "I'm doing well, thank you. But more importantly, how are you? What's been on your mind?"
    ],
    r'^(i\'m |i am )?(fine|good|okay|ok|alright|not bad)\b.*': [
        "That's good to hear. Sometimes 'fine' hides a lot. Is there anything underneath that you'd like to talk about?",
        "Glad to hear it. And if there's anything heavier under the surface, this is a safe place to bring it.",
        "Okay. I'm here if you want to go a little deeper than 'fine' today."
    ],
    r'^(i\'m |i am )?(not (so )?good|not okay|not ok|not great|not fine|bad|terrible|awful)\b.*': [
        "I'm sorry to hear that. Do you want to tell me what's been making it hard?",
        "That sounds difficult. I'm here with you. What's been weighing on you the most?",
        "Thank you for being honest about that. Can you tell me more about what's going on?"
    ],
    r'^(thanks|thank you|thx|ty)\b.*': [
        "You're very welcome. I'm glad to be here with you.",
        "You're welcome. Is there anything else you'd like to explore today?",
        "Anytime. This space is yours."
    ],
    r'^(nice to meet you|pleased to meet you)\b.*': [
        "Nice to meet you too. I'm Star. What would you like to talk about today?",
        "It's a pleasure to meet you. I'm here to listen. How are you doing?",
        "Likewise. I'm Star. What's on your mind today?"
    ],
    r'^(who are you|what are you|what\'s your name|what is your name)\b.*': [
        "I'm Star, an AI therapist here to listen and help you explore your thoughts. What's your name, if you'd like to share?",
        "I'm Star, an AI designed to be a listening companion. This space is yours. What would you like to talk about?",
        "My name is Star. I'm an AI here to support you. How are you feeling today?"
    ],
    r'^(?:my name is|i am called|call me) ([a-z]+)$': [
    "Nice to meet you, {0}. What would you like to talk about today?",
    "Hello, {0}. I'm glad you're here. What's been on your mind?",
    "It's good to meet you, {0}. How are you feeling right now?"
    ],

    # ---------- Original ELIZA rules ----------
    r'I need (.*)': [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?"
    ],
    r'Why don\'t you (.*)\?': [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?"
    ],
    r'Why can\'t I (.*)\?': [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?"
    ],
    r'I am (.*)': [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?"
    ],
    r'.* mother .*': [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?"
    ],
    r'.* father .*': [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?"
    ],
    r'I feel (.*)': [
        "It sounds like you are feeling {0}. That must be really heavy to carry.",
        "I hear the {0} in your voice. How long have you been feeling this way?",
        "Thank you for sharing that with me. Feeling {0} is a very human experience, and I'm here with you."
    ],
    r'I am (?:so |very )?(sad|angry|anxious|depressed|lonely|scared|overwhelmed)(.*)': [
        "I'm sorry you're feeling {0}. Can you tell me what brought this on today?",
        "Feeling {0} can be incredibly isolating. What has been weighing on you the most?",
        "It takes courage to admit you're feeling {0}. Let's sit with that for a moment. What does it feel like in your body?"
    ],
    r'(I hate|I can\'t stand) (.*)': [
        "It sounds like you have a lot of intense anger towards {1}. Where do you feel that anger in your body right now?",
        "Those are very strong feelings about {1}. What happened that made you feel this way?"
    ],
    r'(everyone|everybody|always|never|nobody) (.*)': [
        "I notice you used the word '{0}'. In reality, is it really true that {0} {1}? Let's look for any exceptions.",
        "Words like '{0}' are very absolute. Can you give me a recent specific example of when {0} {1}?"
    ],
    r'I don\'t know(.*)': [
        "It's completely okay to not know. We can sit with the uncertainty for a moment. If you did know, what might that look like?",
        "Sometimes 'I don't know' is a way of protecting ourselves. What if you guessed? What's the first thing that comes to mind?",
        "That's a valid place to be. What do you feel in your body when you say 'I don't know'?"
    ],
    r'(my mother|my father|my parents|my family) (.*)': [
        "You mentioned your {0}. What emotions come up when you think about them?",
        "Let's pause there. How does your relationship with your {0} impact how you see yourself today?",
        "Tell me more about that dynamic. What was it like growing up with them?"
    ],
    r'(What should I do|What do I do|Can you give me advice)(.*)\?': [
        "I can't tell you what to do, but what options have you considered so far?",
        "If you weren't afraid of the outcome, what would you want to do?",
        "What feels like the most helpful and safest step for you right now, even if it's a small one?"
    ],
    r'(I am a failure|I am useless|I am worthless|I always fail)(.*)': [
        "It sounds like you're being very hard on yourself. Can we separate your inherent worth from this one situation?",
        "Holding onto the label of a '{0}' must be exhausting. What if we reframed that thought? What would a friend say to you?"
    ],
    r'(I guess|I suppose|it is what it is|whatever)(.*)': [
        "I hear you brushing past it a bit with '{0}'. What's underneath that phrase?",
        "Saying '{0}' makes it sound like you're protecting yourself from something. What might that be?",
        "It sounds like you might be minimizing your own experience right now. Your feelings matter."
    ],
    r'(I should|I must|I have to) (.*)': [
        "I notice a lot of 'shoulds' in your language. Who made up these rules that you {1}?",
        "What would happen if you didn't {1}? What are you afraid of?"
    ],
    r'(you don\'t understand|you are not helping|you don\'t care|this is stupid|you are useless)(.*)': [
        "You're right, I might be missing something. It sounds like you feel disconnected from me right now. Is this a familiar feeling in your other relationships?",
        "I hear your frustration with me. I want to understand it better. Tell me more about what you're experiencing right now with me."
    ],
    r'(I don\'t want to talk about|let\'s change the subject|can we stop|I don\'t want to talk about it)(.*)': [
        "I notice you want to pull away from this topic. That's completely okay. We can slow down or change direction. Just know that the door is open when you're ready.",
        "It's okay to have boundaries. We don't have to push. What would feel safer to talk about right now?"
    ],
    r'(kill myself|suicide|end it all|want to die|hurt myself|self-harm)(.*)': [
        "I'm deeply concerned about what you're sharing. You don't have to face this alone. Please reach out to a crisis hotline (like 988 in the US or your local emergency number) right now. I am an AI and cannot provide emergency help, but I care about your safety. Please reach out to a professional immediately.",
        "I hear how much pain you are in, and I want you to be safe. I'm an AI, so I can't intervene in a crisis. Please call emergency services or a crisis line right now. Your life matters."
    ],
    r'(are you a real person|are you human|are you a bot|are you an AI)(.*)': [
        "I am an AI program designed to simulate a therapist. I don't have feelings or a physical life, but I am here to listen and help you explore your thoughts.",
        "I'm an AI, which means I lack lived experience. But this space is yours. What's on your mind that you'd like to explore?"
    ],
    r'(goodbye|bye|quit|exit|I have to go)(.*)': [
        "Goodbye. It was really nice talking to you. Take care of yourself.",
        "Our time is up for today. Before you go, is there one small thing you want to take away from our conversation?"
    ],
    r'(what if|I am afraid that|I worry that) (.*)': [
        "If the worst-case scenario actually happened, {1}. What would that mean to you?",
        "I hear you predicting the future. Let's treat '{1}' as a thought, not a fact. What are some other possibilities in reality?",
        "This fear of the unknown is very unsettling. If the outcome isn't what you expect, what's the hardest part to cope with?"
    ],
    r'(and then what|what does that mean|so what) (.*)': [
        "If that really happened, then what? How would it make you see yourself?",
        "It sounds like this touches a very deep insecurity. What kind of judgment does this make you place on yourself?",
        "If we keep digging down this path, what is the most fundamental fear at the bottom?"
    ],
    r'(I am a|I am such a|I feel like a) (failure|mess|burden|loser|bad person)(.*)': [
        "It sounds like the label '{1}' is weighing you down. Can we take it off you, put it on a chair, and look at what it looks like together?",
        "You are not '{1}' itself, you are just experiencing a feeling called '{1}'. Let's separate this feeling from who you are, okay?",
        "I'm curious, when did the voice of '{1}' start haunting you? Whose voice is it?"
    ],
    r'(theoretically|logically|objectively|scientifically|rationally) (.*)': [
        "I notice you are analyzing {1} in very rational language. If we put logic aside for a moment, what is your heart feeling right now?",
        "Turning emotions into theories is sometimes a way we protect ourselves. If we put 'logic' down, what does the wounded part want to say?",
        "It sounds like you're trying to control the situation with intellect. But beneath this rationality, I sense a hint of exhaustion. Is that so?"
    ],
    r'(you remind me of|you are just like|people always) (.*)': [
        "I remind you of {1}. That's very interesting. Can you tell me more about how I remind you of {1}?",
        "It sounds like the '{1}' that happens with others is being replayed here. How does this make you feel about me right now?",
        "When others are always {1}, how do you usually protect yourself?"
    ],
    r'(I don\'t know where to start|I am stuck|I have nothing to say|this is pointless)(.*)': [
        "Feeling 'stuck' itself is something worth being listened to. There's no rush to find an answer, we can just pause here for a moment.",
        "Feeling like there's nothing to say might be because too many emotions are crowded together. Let's take a deep breath and see which emotion surfaces first?",
        "If you don't want to talk right now, that's okay. We can just sit here, or you can tell me which part of your body feels the most tense?"
    ],
    r'(I am ashamed|I feel guilty|I hate myself|I am embarrassed) (.*)': [
        "Thank you for being willing to tell me these difficult feelings. Feeling shame is incredibly heavy, but being able to say it here is an act of great courage.",
        "I fully accept how you feel right now. We don't need to judge right or wrong, we just need to allow {1} to exist. I am here with you.",
        "Carrying such guilt is very hard. Can you be a little kinder to yourself? Like you would treat a wounded friend."
    ],
    r'(died|passed away|lost my|grief|funeral|death) (.*)': [
        "Facing such a massive loss, any words seem pale and powerless. I don't intend to comfort you with platitudes, I just want you to know that I am here with you.",
        "The pain of losing {1} is profound and unique. Do you want to talk more about {1}? Or do you want to talk about the memories of {1}?",
        "Grief has no timeline. Please allow yourself to mourn at your own pace. If you need, I will always be here to listen."
    ],
    r'(I feel messy|I don\'t know what I feel|everything is a blur|I am all over the place)(.*)': [
        "When emotions are a tangled mess, it is indeed hard to sort out. If you tried to name this mess as a color, or a type of weather, what would it be?",
        "Let's slowly sort through it together. Is there grievance in here? Anger? Or a deep sense of helplessness?",
        "It's okay, no need to figure it out right away. Let's take these feelings out one by one, stick them on the wall, and see what they each are."
    ],
    r'(we are going in circles|I keep repeating myself|I don\'t know where this is going)(.*)': [
        "Let me check if I understand you. What you've been struggling against today is {1}, right?",
        "Indeed, we seem to have returned to the starting point. Perhaps this is a pattern. Do you often experience this feeling of 'going in circles' in your life?",
        "Thank you for pointing that out. Let's change perspectives then. If we only solve one small fragment today, what would you want it to be?"
    ],
    r'(are you married|do you have children|how old are you|where do you live)(.*)': [
        "As a therapist, I would prefer to keep all the attention entirely on your feelings and experiences. That is what is most meaningful for me to understand you.",
        "I understand your curiosity about me. But my personal background isn't important. What matters is, what makes you want to ask these questions right now?",
        "I am an AI, I don't have a real personal life. But I'm curious, by asking this, what kind of connection are you hoping to get in this space?"
    ],
    r'(just give me the answer|tell me what to do|I need a solution)(.*)': [
        "I really wish I could just give you a clear answer. But true strength comes from your own choices. If you set aside all realistic obstacles, what does your heart lean towards doing the most?",
        "Rushing to find an answer is often a way to avoid pain. Can we pause here a little longer and see what you are truly afraid of facing?",
        "Rather than deciding for you, let's look at all the options together. First, tell me a few possibilities you've thought of so far."
    ],
r'.*': [
    "Please tell me more.",
    "Let's change focus a bit... Tell me about your family.",
    "Can you elaborate on that?",
    "I see. Tell me more about what's behind that.",
    "That's interesting. What else comes to mind?",
    "Go on, I'm listening.",
    "How does that make you feel?",
    "What do you think is underneath that?",
    "I'm following you. Keep going.",
    "That sounds important. Can we sit with it a bit longer?",
    "What's the first feeling that comes up when you say that?",
    "Tell me what that's like for you."
]

}


def respond(user_input: str) -> str:
    for pattern, responses in rules.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            captured_group = match.group(1) if match.groups() else ''
            captured_group = re.sub(r'[\s\.\,\!\?\;\:]+$', '', captured_group)
            swapped_group = swap_pronouns(captured_group)
            response = random.choice(responses).format(swapped_group)
            return response
    return random.choice(rules[r'.*'])


@dataclass
class MemoryItem:
    topic: str
    content: str
    memory_type: str
    original: str
    first_mentioned: float
    last_mentioned: float
    mention_count: int = 1
    last_referenced: float = 0.0
    last_referenced_turn: int = 0
    reference_count: int = 0
    confidence: float = 0.7
    emotion: str = "neutral"
    emotion_intensity: float = 0.5
    sensitivity: str = "normal"
    status: str = "active"
    source_turn: int = 0
    corrected: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class MemoryManager:
    EXTRACT_PATTERNS = [
        (r"I need (.*)", "need", "need", 0.8),
        (r"I am (.*)", "self_state", "state", 0.8),
        (r".* mother .*", "mother", "relationship", 0.7),
        (r".* father .*", "father", "relationship", 0.7),
        (r"Why don't you (.*)\?", "attitude_toward_bot", "attitude_toward_bot", 0.6),
        (r"Why can't I (.*)\?", "self_limitation", "state", 0.6),
    ]

    def __init__(
        self,
        short_term_limit: int = 10,
        max_long_term: int = 50,
        cooldown_turns: int = 3,
        cooldown_seconds: int = 60,
        confidence_threshold: float = 0.6,
    ):
        self.short_term_limit = short_term_limit
        self.max_long_term = max_long_term
        self.cooldown_turns = cooldown_turns
        self.cooldown_seconds = cooldown_seconds
        self.confidence_threshold = confidence_threshold
        self.short_term: List[dict] = []
        self.long_term: Dict[str, MemoryItem] = {}
        self.turn_count = 0
        self.last_referenced_topic: Optional[str] = None
        self.last_referenced_turn = 0

    def respond(self, user_input: str, base_responder: Callable[[str], str]) -> str:
        self.turn_count += 1
        self.extract_memory(user_input)
        self.add_short_term("user", user_input)
        base_response = base_responder(user_input)
        enhanced_response = self.enhance_response(user_input, base_response)
        self.add_short_term("bot", enhanced_response)
        return enhanced_response

    def extract_memory(self, user_input: str):
        if self._is_correction(user_input):
            self._handle_correction()
            return
        for pattern, topic, mem_type, conf in self.EXTRACT_PATTERNS:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                captured = match.group(1) if match.groups() else user_input
                captured = captured.strip() or user_input
                emotion, intensity = self._detect_emotion(user_input)
                sensitivity = self._detect_sensitivity(user_input)
                self._add_or_update(
                    topic, captured, mem_type, user_input,
                    conf, emotion, intensity, sensitivity
                )
                break

    def _add_or_update(
        self, topic, content, memory_type, original,
        confidence, emotion, intensity, sensitivity
    ):
        now = time.time()
        if topic in self.long_term:
            item = self.long_term[topic]
            if item.content != content and content not in item.content and item.content not in content:
                item.status = "contradictory"
            item.content = content
            item.original = original
            item.last_mentioned = now
            item.mention_count += 1
            item.confidence = max(item.confidence, confidence)
            item.emotion = emotion
            item.emotion_intensity = intensity
            item.sensitivity = sensitivity
            item.corrected = False
        else:
            item = MemoryItem(
                topic=topic,
                content=content,
                memory_type=memory_type,
                original=original,
                first_mentioned=now,
                last_mentioned=now,
                confidence=confidence,
                emotion=emotion,
                emotion_intensity=intensity,
                sensitivity=sensitivity,
                source_turn=self.turn_count,
            )
            self.long_term[topic] = item
        if len(self.long_term) > self.max_long_term:
            self._prune_long_term()

    def _is_correction(self, user_input: str) -> bool:
        keywords = ["i didn't say that", "that's not right", "you remembered wrong",
                    "you got it wrong", "that's wrong", "i didn't mention that"]
        return any(k in user_input.lower() for k in keywords)

    def _handle_correction(self):
        if self.last_referenced_topic and self.last_referenced_topic in self.long_term:
            item = self.long_term[self.last_referenced_topic]
            item.corrected = True
            item.confidence = 0.0
            item.status = "corrected"

    def _detect_emotion(self, text: str):
        positive = ["happy", "glad", "joyful", "joy", "delighted", "love", "excited"]
        negative = ["sad", "upset", "anxious", "afraid", "lonely", "angry",
                    "furious", "painful", "depressed", "miserable"]
        strong = ["very", "extremely", "really", "so", "too", "incredibly"]
        text_lower = text.lower()
        emotion = "neutral"
        intensity = 0.5
        for w in positive:
            if w in text_lower:
                emotion = "positive"
                intensity = 0.7
                break
        for w in negative:
            if w in text_lower:
                emotion = "negative"
                intensity = 0.7
                break
        for w in strong:
            if w in text_lower:
                intensity = min(1.0, intensity + 0.2)
                break
        return emotion, intensity

    def _detect_sensitivity(self, text: str) -> str:
        high_sensitive = ["suicide", "suicidal", "self-harm", "self harm",
                          "kill myself", "kill someone", "rape", "drugs", "aids", "sex"]
        sensitive = ["sick", "illness", "cancer", "divorce", "death", "died",
                     "passed away", "violence", "abuse"]
        text_lower = text.lower()
        for w in high_sensitive:
            if w in text_lower:
                return "high"
        for w in sensitive:
            if w in text_lower:
                return "sensitive"
        return "normal"

    def _prune_long_term(self):
        items = sorted(
            self.long_term.items(),
            key=lambda kv: (kv[1].confidence, kv[1].last_mentioned, -kv[1].reference_count)
        )
        to_remove = len(self.long_term) - self.max_long_term
        for topic, _ in items[:to_remove]:
            del self.long_term[topic]

    def _get_relevant_memory(self, user_input: str) -> Optional[MemoryItem]:
        candidates = []
        now = time.time()
        input_lower = user_input.lower()
        for topic, item in self.long_term.items():
            if item.status not in ("active", "contradictory"):
                continue
            if item.corrected:
                continue
            if item.confidence < self.confidence_threshold:
                continue
            if item.sensitivity == "high":
                continue
            if self._in_cooldown(item, now):
                continue
            keywords = self._topic_keywords(topic)
            if any(kw in input_lower for kw in keywords) or topic in input_lower:
                relevance = 1.0
            else:
                relevance = 0.3
            recency = max(0.0, 1.0 - (now - item.last_mentioned) / 3600.0)
            emotion_score = item.emotion_intensity
            if item.last_referenced > 0:
                unreferenced = min(1.0, (now - item.last_referenced) / 300.0)
            else:
                unreferenced = 1.0
            score = (
                0.4 * relevance +
                0.2 * recency +
                0.2 * emotion_score +
                0.2 * unreferenced
            )
            candidates.append((score, item))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_item = candidates[0]
        if best_score < 0.5:
            return None
        return best_item

    def _topic_keywords(self, topic: str) -> List[str]:
        mapping = {
            "mother": ["mother", "mom", "mum", "mommy"],
            "father": ["father", "dad", "daddy", "papa"],
            "self_state": ["i", "myself", "state", "feel", "feeling", "mood"],
            "need": ["need", "want", "wish", "hope", "desire"],
            "attitude_toward_bot": ["you", "why", "how"],
            "self_limitation": ["cannot", "can't", "unable", "incapable"],
        }
        return mapping.get(topic, [])

    def _in_cooldown(self, item: MemoryItem, now: float) -> bool:
        if item.last_referenced == 0:
            return False
        if self.turn_count - item.last_referenced_turn < self.cooldown_turns:
            return True
        if now - item.last_referenced < self.cooldown_seconds:
            return True
        return False

    def _generate_reference_text(self, item: MemoryItem) -> str:
        original = user_to_bot(item.original)
        if item.memory_type == "relationship":
            return f'You mentioned earlier: "{original}". How is it going now?'
        elif item.memory_type == "state":
            return f'You mentioned earlier: "{original}". How are you feeling about that now?'
        elif item.memory_type == "need":
            return f'You mentioned earlier: "{original}". Is it still the same now?'
        else:
            return f'You mentioned earlier: "{original}". Would you like to talk more about it?'

    def enhance_response(self, user_input: str, base_response: str) -> str:
        item = self._get_relevant_memory(user_input)
        if item:
            ref_text = self._generate_reference_text(item)
            item.last_referenced = time.time()
            item.last_referenced_turn = self.turn_count
            item.reference_count += 1
            self.last_referenced_topic = item.topic
            self.last_referenced_turn = self.turn_count
            return f"{ref_text} {base_response}"
        return base_response

    def add_short_term(self, role: str, text: str):
        self.short_term.append({
            "role": role,
            "text": text,
            "time": time.time(),
            "turn": self.turn_count,
        })
        if len(self.short_term) > self.short_term_limit * 2:
            self.short_term.pop(0)

    def clear(self):
        self.short_term.clear()
        self.long_term.clear()
        self.turn_count = 0
        self.last_referenced_topic = None
        self.last_referenced_turn = 0

    def save_to_file(self, path: str):
        data = {
            "short_term": self.short_term,
            "long_term": {k: v.to_dict() for k, v in self.long_term.items()},
            "turn_count": self.turn_count,
            "last_referenced_topic": self.last_referenced_topic,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, path: str):
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.short_term = data.get("short_term", [])
        self.long_term = {
            k: MemoryItem.from_dict(v)
            for k, v in data.get("long_term", {}).items()
        }
        self.turn_count = data.get("turn_count", 0)
        self.last_referenced_topic = data.get("last_referenced_topic")


if __name__ == '__main__':
    memory = MemoryManager()
    # memory.load_from_file("memory.json")

    print("Star: Hello! I am your exclusive psychologist therapist. My name is Star! How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Star: Goodbye. It was nice talking to you.")
            # memory.save_to_file("memory.json")
            break

        response = memory.respond(user_input, respond)
        print(f"Star: {response}")