import crianza
import crianza.compiler as cc
import crianza.genetic as gp
import random

def inverse_weighted_tanimoto(results, goals, weights):
    return 1.0 - gp.weighted_tanimoto(results, goals, weights)

def gpfind(input, check, silent=True, **randomize_kw):
    class GPFind(gp.GeneticMachine):
        def __init__(self, code=[]):
            super(GPFind, self).__init__(code)
            self.gp_input = input()

        def new(self, *args, **kw):
            return GPFind(*args, **kw)

        def randomize(self, **kw):
            kw = kw.copy()
            kw.update(randomize_kw)
            return super(GPFind, self).randomize(**kw)

        def setUp(self):
            self.gp_input = input()
            self.original_code = self.code
            self.code = [cc.make_embedded_push(self.gp_input)] + self.code
            # TODO: Run several times

        def tearDown(self):
            self.code = self.original_code
            self.original_code = None

        def score(self):
            def asint(x):
                try:
                    return int(x)
                except:
                    pass
                return 0

            goals = {
                "result": (0.8, asint(check(self.gp_input, asint(self.top))), asint(True)),
                "no errors": (0.1, 0, int(self._error)),
                "empty return stack": (0.02, 0, len(self.return_stack)),
                "one stack result": (0.02, 1, len(self.stack)),
                "code length": (0.06, 1, int(1<len(self.code)<100))
            }

            weights = [v[0] for v in goals.values()]
            wanted = [v[1] for v in goals.values()]
            actual = [v[2] for v in goals.values()]
            return 1.0 - gp.weighted_tanimoto(actual, wanted, weights)

        @staticmethod
        def stop(iterations, generation):
            best = sorted(generation, key=lambda m: m.score())
            best = best[:min(len(best),3)]
            return gp.average(best, lambda s: s.score()) < 0.0000001

    survivors = gp.iterate(GPFind, GPFind.stop, machines=100, silent=silent)
    return survivors[0].code

if __name__ == "__main__":
    print("Finding program that doubles numbers ...")
    code = gpfind(lambda: random.randint(0,100), lambda i,o: i==o/2,
                  instruction_ratio=0.75, number_string_ratio=1.0)
    print("Found: %s" % crianza.code_to_string(code))
