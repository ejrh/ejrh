import random


class Action(object):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return self.name

COOPERATE = Action('COOPERATE')
DEFECT = Action('DEFECT')


class Player(object):
    """A player of Prisoner's Dilemma.  Could be a human or one of a variety of AI players."""
    
    def __init__(self, name=None):
        if name is None:
                name = '%s%s' % (type(self).__name__, id(self))
        self.name = name
        self.score = 0
    
    def update(self, action):
        """Update the player with their opponent's last action."""
        raise NotImplementedError
    
    def choose(self):
        """Choose an action."""
        raise NotImplementedError
    
    def award(self, winnings):
        self.score += winnings
    
    def __repr__(self):
        return self.name


class MarkovianAI(Player):
    def __init__(self, patterns, initial_history=[]):
        super(MarkovianAI, self).__init__()
        self.patterns = patterns
        self.initial_history = list(initial_history)
        self.reset()

    def clone(self):
        c = MarkovianAI(self.patterns, self.initial_history)
        return c

    def reset(self):
        self.history = list(self.initial_history)
    
    def update(self, action):
        self.history.append(action)
        self.history.pop(0)
        #print self.name, 'Appended %s, history is now %s' % (action, self.history)
    
    def choose(self):
        x = random.random()
        l = len(self.history)
        #print self.name, 'History is %s' % self.history
        while l >= 0:
            p = len(self.history) - l
            k = tuple(self.history[p:])
            try:
                if x >= self.patterns[k]:
                    action = DEFECT
                else:
                    action = COOPERATE
                #print self.name, 'Applied %s against pattern %s for key %s, giving %s' % (x, self.patterns[k], k, action)
                return action
            except KeyError:
                l -= 1


class ConstantAI(MarkovianAI):
    """A player that always does the same thing."""
    
    def __init__(self, constant):
        if constant is COOPERATE:
            threshold = 1.0
        else:
            threshold = 0.0
        patterns = {
            (): threshold
        }
        super(ConstantAI, self).__init__(patterns)
        self.name += '(%s)' % constant
    
    def clone(self):
        if self.patterns[()] >= 0.5:
            constant = COOPERATE
        else:
            constant = DEFECT
        c = ConstantAI(constant)
        return c


class TitForTatAI(MarkovianAI):
    """A player that always chooses the last action of its opponent."""
    
    def __init__(self, initial):
        patterns = {
            (COOPERATE,): 1.0,
            (DEFECT,): 0.0,
        }
        super(TitForTatAI, self).__init__(patterns, [initial])

    def clone(self):
        c = TitForTatAI(self.initial_history[0])
        return c

class RandomAI(MarkovianAI):
    """A player that chooses randomly between COOPERATE and DEFECT."""
    
    def __init__(self, threshold=0.5):
        patterns = {
            (): threshold
        }
        super(RandomAI, self).__init__(patterns)
        self.name += '(%0.2f)' % threshold

    def clone(self):
        c = RandomAI(self.patterns[()])
        return c


class Match(object):
    def __init__(self, matrix):
        self.matrix = matrix
        self.players = []
        self.scores = []
    
    def add_player(self, player):
        self.players.append(player)
        self.scores.append(0)
    
    def fight(self):
        choice1 = self.players[0].choose()
        choice2 = self.players[1].choose()
        #print 'Choices:', choice1, choice2
        payoff1, payoff2 = self.matrix[(choice1, choice2)]
        #print 'Payoffs:', payoff1, payoff2
        self.players[0].update(choice2)
        self.players[1].update(choice1)
        self.players[0].award(payoff1)
        self.players[1].award(payoff2)
        self.scores[0] += payoff1
        self.scores[1] += payoff2
    
    def run(self, iterations):
        for p in self.players:
            p.reset()
        for i in range(iterations):
            self.fight()
    
    def report(self):
        return str(self.scores)



DEFAULT_MATRIX = {
    (COOPERATE, COOPERATE): (3,3),
    (COOPERATE, DEFECT): (1,4),
    (DEFECT, COOPERATE): (4,1),
    (DEFECT, DEFECT): (2,2),
}


class Evolution(object):
    def __init__(self):
        pass
    
    def run(self, population):
        for p1 in population:
            for p2 in population:
                if p1 is p2:
                    continue
                
                match = Match(DEFAULT_MATRIX)
                match.add_player(p1)
                match.add_player(p2)
                match.run(10)
                #print match.report()

        total_score = float(sum(p.score for p in population))
        new_pop = []
        for i in range(20):
            x = random.random()
            for p in population:
                if p.score/total_score >= x:
                    new_pop.append(p)
                    break
                else:
                    x -= p.score/total_score
        
        return new_pop


def main():
    population = [
        ConstantAI(COOPERATE),
        ConstantAI(DEFECT),
        RandomAI(),
        RandomAI(0.1),
        RandomAI(0.9),
        TitForTatAI(COOPERATE),
        TitForTatAI(DEFECT),
    ]
    for i in range(100):
        evolution = Evolution()
        population = evolution.run(population)
    print population

if __name__ == '__main__':
    main()
