import os


# 全局配置类
# -----------------------------------------------------------------------------
class Config(object):
    pdf_dir = os.path.join('data', 'pdf')
    # 查询分类设置，全部分类请参照 https://arxiv.org/help/api/user-manual#subject_classifications
    search_cat = ('cs.AI',
                  'cs.AR',
                  'cs.CC',
                  'cs.CE',
                  'cs.CG',
                  'cs.CL',
                  'cs.CR',
                  'cs.CV',
                  'cs.CY',
                  'cs.DB',
                  'cs.DC',
                  'cs.DL',
                  'cs.DM',
                  'cs.DS',
                  'cs.ET',
                  'cs.FL',
                  'cs.GL',
                  'cs.GR',
                  'cs.GT',
                  'cs.HC',
                  'cs.IR',
                  'cs.IT',
                  'cs.LG',
                  'cs.LO',
                  'cs.MA',
                  'cs.MM',
                  'cs.MS',
                  'cs.NA',
                  'cs.NE',
                  'cs.NI',
                  'cs.OH',
                  'cs.OS',
                  'cs.PF',
                  'cs.PL',
                  'cs.RO',
                  'cs.SC',
                  'cs.SD',
                  'cs.SE',
                  'cs.SI',
                  'cs.SY',
                  )
