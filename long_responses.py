import random

R_EATING = "I don't like eating anything because I'm a bot obviously!"
R_ADVICE = "If I were you, I would go to the internet and type exactly what you wrote there!"


def unknown():
    response = ["I'm sorry, I couldn't understand that. Can you please rephrase or provide more details?",
                "Apologies, I'm not sure what you mean. Could you please try rephrasing?",
                "It seems I'm unable to comprehend. Could you provide more context or rephrase?",
                "I'm still learning and might not understand everything. Could you try saying that in a different way?"][
        random.randrange(4)]
    return response