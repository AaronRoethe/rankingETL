import numpy as np
import pandas as pd

from .business_prioirty import company_busines_lines
from .user_input import load_custom_skills
from .utils import join_tables


def rank(df=pd.DataFrame, new_col=str, groups=list, rank_cols=dict):
    sort_columns = groups + [*rank_cols.keys()]
    ascending = [True] * len(groups) + [*rank_cols.values()]

    df.sort_values(sort_columns, ascending=ascending, inplace=True)
    df[new_col] = 1
    df[new_col] = df.groupby(groups)[new_col].cumsum()
    return df


def parent_child_link(df, parent: str, child: str):
    df[child] = df[child].apply(lambda x: str(x))
    df["Matches"] = (
        df.groupby(["Group", parent])[child]
        .transform(lambda x: "|".join(x))
        .apply(lambda x: x[:3000])
    )
    return df


def stack_inventory(df, grouping):
    rank_cols = "test"
    # group & rank highest value org
    find_parent = rank(df, "overall_rank", ["Skill", grouping], rank_cols)

    # top overall per group = parent
    f1 = find_parent.overall_rank == 1
    find_parent["parent"] = np.where(f1, 1, 0)

    # rank parent orgs
    full_rank = rank(find_parent, "Score", ["Skill", "parent"], rank_cols)

    linked = parent_child_link(full_rank, grouping)
    return linked


def split_by_grouping(df):
    pass


def custom_skill_rank(table, skill, custom_ranking):
    skill = table[table.Skill == skill].copy()
    scored_skill = rank(skill, "Score", ["groups", "parent"], custom_ranking)
    return join_tables(scored_skill, table)


def scored_inventory(df):
    # split regular inventory
    inventory = split_by_grouping(df)

    split = "spit"
    custom_inventory = inventory[inventory.Skill == split].copy()
    # if data available in business_lines.json load into scoring logic

    business = company_busines_lines()
    business.reverse()
    if isinstance(business, list):
        custom_inventory = load_custom_skills(custom_inventory, business)
        for line in business:
            custom_inventory = custom_skill_rank(
                custom_inventory, line.skill, line.scoring
            )

    post_inventory = join_tables(custom_inventory, inventory)
    return post_inventory
