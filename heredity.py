import csv
import itertools
import sys

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # # Check for proper usage
    # if len(sys.argv) != 2:
    #     sys.exit("Usage: python heredity.py data.csv")
    # people = load_data(sys.argv[1])

    people = load_data("data/family0.csv")

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def genes_dict(people, one_gene, two_genes):
    """
    Returns a dictionary that maps each person to the
    number of genes based on one_gene and two_genes set.
    """
    genes = dict()

    for person in people:
        if person in one_gene:
            genes[person] = 1

        elif person in two_genes:
            genes[person] = 2

        else:
            genes[person] = 0

    return genes


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.

    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """

    # Number of genes in the given scenario.
    genes = genes_dict(people, one_gene, two_genes)

    prob_list = []

    for person in people:
        prob = 1

        # Two genes in the scenario:
        if genes[person] == 2:

            # Has parents:
            if people[person]["mother"] and people[person]["father"]:

                for parent in [people[person]["mother"], people[person]["father"]]:

                    if genes[parent] == 2:
                        prob *= 1 - PROBS["mutation"]
                    
                    elif genes[parent] == 1:
                        prob *= 0.5 # Mutations cancel out in this case

                    else:
                        prob *= PROBS["mutation"]
                    
            # Has no parents:
            else:
                prob *= PROBS["gene"][2]
        
        # One gene in the scenario:
        elif genes[person] == 1:
            
            # Has parents:
            if people[person]["mother"] and people[person]["father"]:

                sum = genes[people[person]["mother"]] + genes[people[person]["father"]]
                
                if sum == 4:
                    prob *= 2 * PROBS["mutation"] * (1 - PROBS["mutation"])

                elif sum == 3:
                    prob *= 0.5 # All mutations cancel out

                elif sum == 2:
                    
                    if genes[people[person]["mother"]] == 1:
                        prob *= 0.5 # All mutations cancel out

                    else:
                        prob *= 1 - 2 * PROBS["mutation"] + 2 * PROBS["mutation"]**2

                elif sum == 1:
                    prob *= 0.5 # All mutations cancel out

            # Has no parents:
            else:
                prob *= PROBS["gene"][1]

        # Zero gene in the scenario:
        else:
            
            # Has parents:
            if people[person]["mother"] and people[person]["father"]:
                
                for parent in [people[person]["mother"], people[person]["father"]]:

                    if genes[parent] == 2:
                        prob *= PROBS["mutation"]

                    elif genes[parent] == 1:
                        prob *= 0.5

                    else:
                        prob *= 1 - PROBS["mutation"]

            # Has no parents:
            else:
                prob *= PROBS["gene"][0]

        # Traits:
        prob *= PROBS["trait"][genes[person]][person in have_trait]

        prob_list.append(prob)

    joint = 1
    for prob in prob_list:
        joint *= prob

    return joint


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    
    genes = genes_dict(probabilities, one_gene, two_genes)

    for person in probabilities:
        probabilities[person]["gene"][genes[person]] += p
        probabilities[person]["trait"][person in have_trait] += p


def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    
    for person in probabilities:
        for dist in probabilities[person]:
            sum = 0

            for value in probabilities[person][dist]:
                sum += probabilities[person][dist][value]
            
            for value in probabilities[person][dist]:
                probabilities[person][dist][value] /= sum


if __name__ == "__main__":
    main()
