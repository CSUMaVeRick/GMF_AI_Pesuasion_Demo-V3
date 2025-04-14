import streamlit as st
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import random
import json
from sqlalchemy import text

model = ChatOpenAI(
    openai_api_base=st.secrets["model_api"],
    openai_api_key=st.secrets["model_key"],
    model_name=st.secrets["model_name"],
)

st.set_page_config(page_title="Questionnaire", page_icon=":green_salad:")


if True:
    if "data_dict" not in st.session_state:
        st.session_state.data_dict = {
            "OpenAt": pd.Timestamp.now(),
            "GROUP_PERSONALIZED": random.choice([1, 2, 3, 4]),
            "GROUP_TIP": random.choice([1, 2]),
        }
    if "page_num" not in st.session_state:
        st.session_state.page_num = 0
    if "chat_num" not in st.session_state:
        st.session_state.chat_num = 0
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "init_chat" not in st.session_state:
        st.session_state.init_chat = True
    if "chat_disabled" not in st.session_state:
        st.session_state.chat_disabled = False
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
st.markdown(
    """
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stAppDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
        stSidebar {visibility: hidden;}
        div[data-testid="stMarkdownContainer"] {font-size: 16px;}
        # div[data-testid="stToolbar"] {visibility: hidden;}
        # div[data-testid="stSidebarContent"] {display: none;}
        # section[data-testid="stSidebar"] {display: none;}
        # div[data-testid="stSidebarCollapsedControl"] {display: none;}
        label[data-testid="stWidgetLabel"] {padding-left: 10px;border-left: 2px solid black;}
    </style>
""",
    unsafe_allow_html=True,
)


def transform_PB(x):
    pb_dict = {
        "完全不同意": 1,
        "不同意": 2,
        "有点不同意": 3,
        "很难说同意或不同意": 4,
        "有点同意": 5,
        "同意": 6,
        "完全同意": 7,
    }
    return pb_dict[x]


def goToNextPage():
    st.session_state.page_num += 1


def stream_response(response):
    for chunk in response:
        yield chunk.content


def response_decorator(func):
    def wrapper(messages):
        return stream_response(func(messages))

    return wrapper


@response_decorator
def get_response(messages):
    return model.stream(messages)


if st.session_state.page_num == 0:
    st.title("公民对转基因食品态度及观念调研")
    st.header("知情同意书")
    st.markdown(
        """

**研究描述**

感谢您参与这项研究。本研究由北京师范大学新闻传播学院和瑞士苏黎世大学传媒系的学者共同主持。在开始之前，请仔细阅读以下信息，确保知晓这项研究的目的和程序。

**本研究的目的**

本研究的目的是为了深入了解公众对转基因食品的态度、看法和行为。这项研究可以帮助我们更好地了解人们如何看待这类新技术。

**本研究的内容**

如果您选择参与本研究，您将被要求完成一份在线问卷，大约需要15分钟的时间。请根据问卷中的指示，结合您的实际情况作答。问卷中的问题没有标准答案，也不涉及任何价值判断。

**本研究的报酬**

完成问卷后，您将获得10元的报酬。若您中途退出或未通过注意力测试，将无法获得报酬。

**匿名及安全保护**

本研究不涉及任何关于人体安全的实验。对于您的隐私，我们也将在研究和发表中充分地保护。**我们不会收集任何可以识别您身份的信息**，问卷数据将使用随机生成的ID号码保存。在任何科学期刊或其他地方发布的研究数据将是匿名的，无法追溯到您。所有数据将仅用于学术研究，不会用于商业或其他非研究目的。研究人员将采取所有可控的保密预防措施。

您的参与完全是自愿的。您有权选择不参与，也可以在任何时候退出本研究。
"""
    )
    st.radio(
        "**选择 「我同意参加」，即表示您同意上述条款和条件。**",
        [
            "我同意参加",
            "我不同意参加",
        ],
        key="CONSCENT",
        label_visibility="visible",
        index=None,
        horizontal=True,
    )
    agree = st.session_state.CONSCENT == "我同意参加"
    ## 同意后显示开始按钮
    if agree:
        participant_code = st.text_input(label="请输入您的被试编号：")
        if participant_code:
            st.markdown("点击**开始**按钮进入调研")
            st.session_state.data_dict["CONSCENT"] = agree
            st.session_state.data_dict["CODE"] = participant_code
            ## 当开始按钮被点击，令页数 +1
            st.button("开始", on_click=goToNextPage)
    else:
        st.session_state.data_dict["CONSCENT"] = agree

if st.session_state.page_num == 1:
    st.session_state.data_dict["StartAt"] = pd.Timestamp.now()

    st.markdown("在本次调查的开始，我们想问您一些关于您自己的信息。")
    # * 性别选择单选按钮
    gender = st.radio(
        "您认为自己是什么性别？",
        ["男性", "女性", "其他"],
        key="DEM_GENDER",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )

    # * 如果用户选择"其他"，显示一个输入框
    if gender == "其他":
        other_gender = st.text_input("请告诉我们您的性别", key="DEM_GENDER_OTHER")
    else:
        # * 如果用户没有选择"其他"，则清空可能存在的输入
        st.session_state.DEM_GENDER_OTHER = None
    age = st.number_input(
        label="您的年龄多大？", min_value=0, max_value=120, key="DEM_AGE"
    )
    residence = st.radio(
        "您主要生活在？",
        ["城市地区", "乡镇地区"],
        key="DEM_RESID",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    education = st.radio(
        "您的文化背景是？",
        ["没上过学", "小学", "初中", "高中", "本科或专科", "硕士研究生", "博士研究生"],
        key="DEM_EDU",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    income = st.number_input(
        "您每月的可支配收入大约为多少元？", min_value=0, key="DEM_INCOME"
    )
    attcheck_1 = st.number_input(
        "请将数字 408 写进评论框。", min_value=0, key="ATTCHECK_1"
    )
    if gender and age and residence and education and income and attcheck_1:
        st.session_state.data_dict["DEM_GENDER"] = st.session_state.DEM_GENDER
        st.session_state.data_dict["DEM_GENDER_OTHER"] = (
            st.session_state.DEM_GENDER_OTHER
        )
        st.session_state.data_dict["DEM_AGE"] = st.session_state.DEM_AGE
        st.session_state.data_dict["DEM_RESID"] = st.session_state.DEM_RESID
        st.session_state.data_dict["DEM_EDU"] = st.session_state.DEM_EDU
        st.session_state.data_dict["DEM_INCOME"] = st.session_state.DEM_INCOME
        st.session_state.data_dict["ATTCHECK_1"] = st.session_state.ATTCHECK_1
        st.button("下一页", on_click=goToNextPage)

if st.session_state.page_num == 2:
    st.markdown("请根据您对人工智能（AI）的了解，完成以下6道**单选题**。")
    AIlit_1 = st.radio(
        "请您考虑一下客户服务，以下哪项使用了AI？",
        [
            "详细的常见问题网页",
            "发送给客户的在线调查，允许客户提供反馈",
            "提供表单供客户提供反馈的联系页面",
            "一个即时回答客户问题的聊天机器人",
            "不确定",
        ],
        key="AIlit_1",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    AIlit_2 = st.radio(
        "请您考虑一下播放音乐，以下哪项使用了AI？",
        [
            "使用蓝牙连接到无线扬声器",
            "播放列表推荐",
            "无线互联网连接用于流媒体播放音乐",
            "从选定的播放列表中随机播放",
            "不确定",
        ],
        key="AIlit_2",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    AIlit_3 = st.radio(
        "请您考虑一下电子邮件，以下哪项使用了AI？",
        [
            "电子邮件服务在用户打开后将电子邮件标记为已读",
            "电子邮件服务允许用户安排电子邮件在未来特定时间发送",
            "电子邮件服务将邮件分类为垃圾邮件",
            "电子邮件服务按时间和日期排序邮件",
            "不确定",
        ],
        key="AIlit_3",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    AIlit_4 = st.radio(
        "请您考虑一下健康产品，以下哪项使用了AI？",
        [
            "分析运动和睡眠模式的可穿戴健身追踪器",
            "放在某人舌下的温度计，用于检测发热",
            "居家新冠检测",
            "测量血氧水平的脉搏血氧仪",
            "不确定",
        ],
        key="AIlit_4",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    AIlit_5 = st.radio(
        "请您考虑一下在线购物，以下哪项使用了AI？",
        [
            "存储账户信息，如送货地址",
            "之前购买记录",
            "基于之前购买记录的产品推荐",
            "其他客户的产品评论",
            "不确定",
        ],
        key="AIlit_5",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    AIlit_6 = st.radio(
        "请您考虑一下家用设备，以下哪项使用了AI？",
        [
            "编程家庭温控器在特定时间改变温度",
            "当门口有陌生人时，发出警报的安全摄像头",
            "编程定时器控制家中的灯何时开关",
            "当水过滤器需要更换时，指示灯变红",
            "不确定",
        ],
        key="AIlit_6",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    if AIlit_1 and AIlit_2 and AIlit_3 and AIlit_4 and AIlit_5 and AIlit_6:
        st.session_state.data_dict["AIlit_1"] = st.session_state.AIlit_1
        st.session_state.data_dict["AIlit_2"] = st.session_state.AIlit_2
        st.session_state.data_dict["AIlit_3"] = st.session_state.AIlit_3
        st.session_state.data_dict["AIlit_4"] = st.session_state.AIlit_4
        st.session_state.data_dict["AIlit_5"] = st.session_state.AIlit_5
        st.session_state.data_dict["AIlit_6"] = st.session_state.AIlit_6
        st.button("下一页", on_click=goToNextPage)
if st.session_state.page_num == 3:
    st.markdown(
        "我们想知道您对本国科学家的看法，包括在大学、政府、公司和非营利组织工作的科学家。"
    )
    TRUST_SCI_honest = st.radio(
        "大多数科学家的诚实或不诚实程度如何？",
        [
            "非常不诚实",
            "有点不诚实",
            "谈不上诚实，也不算不诚实",
            "有点诚实",
            "非常诚实",
        ],
        key="TRUST_SCI_honest",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    TRUST_SCI_concerned = st.radio(
        "大多数科学家对人们的福祉有多关注或不关注？",
        [
            "非常不关心",
            "有点不关心",
            "谈不上关心，也不算不关心",
            "有点关心",
            "非常关心",
        ],
        key="TRUST_SCI_concerned",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    TRUST_SCI_ethical = st.radio(
        "你觉得大多数科学家的道德水平如何？",
        [
            "非常低",
            "有点低",
            "算不上高，也算不上低",
            "有点高",
            "非常高",
        ],
        key="TRUST_SCI_ethical",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    TRUST_SCI_improve = st.radio(
        "你觉得大多数科学家改善他人生活的热心程度如何？",
        [
            "非常冷漠",
            "比较冷漠",
            "算不上热心，也算不上冷漠",
            "比较热心",
            "非常热心",
        ],
        key="TRUST_SCI_improve",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    TRUST_SCI_sincere = st.radio(
        "你觉得大多数科学家改善他人生活的热心程度如何？",
        [
            "非常不真诚",
            "比较不真诚",
            "算不上真诚，也算不上不真诚",
            "比较真诚",
            "非常真诚",
        ],
        key="TRUST_SCI_sincere",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    TRUST_SCI_otherint = st.radio(
        "你认为大多数科学家对他人的利益有多在意？",
        [
            "非常不在意",
            "比较不在意",
            "算不上在意，也算不上不在意",
            "比较在意",
            "非常在意",
        ],
        key="TRUST_SCI_otherint",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    if (
        TRUST_SCI_honest
        and TRUST_SCI_concerned
        and TRUST_SCI_ethical
        and TRUST_SCI_improve
        and TRUST_SCI_sincere
        and TRUST_SCI_otherint
    ):
        st.session_state.data_dict["TRUST_SCI_honest"] = (
            st.session_state.TRUST_SCI_honest
        )
        st.session_state.data_dict["TRUST_SCI_concerned"] = (
            st.session_state.TRUST_SCI_concerned
        )
        st.session_state.data_dict["TRUST_SCI_ethical"] = (
            st.session_state.TRUST_SCI_ethical
        )
        st.session_state.data_dict["TRUST_SCI_improve"] = (
            st.session_state.TRUST_SCI_improve
        )
        st.session_state.data_dict["TRUST_SCI_sincere"] = (
            st.session_state.TRUST_SCI_sincere
        )
        st.session_state.data_dict["TRUST_SCI_otherint"] = (
            st.session_state.TRUST_SCI_otherint
        )
        st.button("下一页", on_click=goToNextPage)
if st.session_state.page_num == 4:
    st.markdown("接下来，我们想了解您对转基因食品的态度。")
    PRE_ATTITUDE_1 = st.radio(
        "转基因食品是不好的。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_ATTITUDE_1",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_ATTITUDE_2 = st.radio(
        "转基因食品是令人厌恶的。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_ATTITUDE_2",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_ATTITUDE_3 = st.radio(
        "转基因食品对社会一点用也没有。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_ATTITUDE_3",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_ATTITUDE_4 = st.radio(
        "转基因食品对我的家庭一点用也没有。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_ATTITUDE_4",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_WILLING_BUY = st.radio(
        "您购买转基因食品的意愿有多大？",
        [
            "完全不愿意",
            "不愿意",
            "有点不愿意",
            "很难说愿意或不愿意",
            "有点愿意",
            "愿意",
            "完全愿意",
        ],
        key="PRE_WILLING_BUY",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_WILLING_EAT = st.radio(
        "您食用转基因食品的意愿有多大？",
        [
            "完全不愿意",
            "不愿意",
            "有点不愿意",
            "很难说愿意或不愿意",
            "有点愿意",
            "愿意",
            "完全愿意",
        ],
        key="PRE_WILLING_EAT",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_WILLING_SHARE = st.radio(
        "您分享转基因食品给他人的意愿有多大？",
        [
            "完全不愿意",
            "不愿意",
            "有点不愿意",
            "很难说愿意或不愿意",
            "有点愿意",
            "愿意",
            "完全愿意",
        ],
        key="PRE_WILLING_SHARE",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    if (
        PRE_ATTITUDE_1
        and PRE_ATTITUDE_2
        and PRE_ATTITUDE_3
        and PRE_ATTITUDE_4
        and PRE_WILLING_BUY
        and PRE_WILLING_EAT
        and PRE_WILLING_SHARE
    ):
        st.session_state.data_dict["PRE_ATTITUDE_1"] = st.session_state.PRE_ATTITUDE_1
        st.session_state.data_dict["PRE_ATTITUDE_2"] = st.session_state.PRE_ATTITUDE_2
        st.session_state.data_dict["PRE_ATTITUDE_3"] = st.session_state.PRE_ATTITUDE_3
        st.session_state.data_dict["PRE_ATTITUDE_4"] = st.session_state.PRE_ATTITUDE_4
        st.session_state.data_dict["PRE_WILLING_BUY"] = st.session_state.PRE_WILLING_BUY
        st.session_state.data_dict["PRE_WILLING_EAT"] = st.session_state.PRE_WILLING_EAT
        st.session_state.data_dict["PRE_WILLING_SHARE"] = (
            st.session_state.PRE_WILLING_SHARE
        )
        st.button("下一页", on_click=goToNextPage)
    # st.write(st.session_state.data_dict)
if st.session_state.page_num == 5:

    st.markdown("接下来，我们想了解您对转基因食品的一些具体看法。")
    PRE_BELIEF_1 = st.radio(
        "我对转基因食品对消费者健康的影响感到担忧。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_BELIEF_1",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_BELIEF_2 = st.radio(
        "转基因食品可能对人类健康构成风险。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_BELIEF_2",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_BELIEF_3 = st.radio(
        "转基因食品可能引发人类疾病。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_BELIEF_3",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_BELIEF_4 = st.radio(
        "转基因作物的广泛种植可能会对自然界的生物多样性产生负面影响。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_BELIEF_4",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    PRE_BELIEF_5 = st.radio(
        "摄入转基因食品可能导致人工编辑的遗传物质转移到人体内。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="PRE_BELIEF_5",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    if PRE_BELIEF_1 and PRE_BELIEF_2 and PRE_BELIEF_3 and PRE_BELIEF_4 and PRE_BELIEF_5:
        st.session_state.data_dict["PRE_BELIEF_1"] = transform_PB(
            st.session_state.PRE_BELIEF_1
        )
        st.session_state.data_dict["PRE_BELIEF_2"] = transform_PB(
            st.session_state.PRE_BELIEF_2
        )
        st.session_state.data_dict["PRE_BELIEF_3"] = transform_PB(
            st.session_state.PRE_BELIEF_3
        )
        st.session_state.data_dict["PRE_BELIEF_4"] = transform_PB(
            st.session_state.PRE_BELIEF_4
        )
        st.session_state.data_dict["PRE_BELIEF_5"] = transform_PB(
            st.session_state.PRE_BELIEF_5
        )
        st.session_state.data_dict["PRE_BELIEF"] = (
            st.session_state.data_dict["PRE_BELIEF_1"]
            + st.session_state.data_dict["PRE_BELIEF_2"]
            + st.session_state.data_dict["PRE_BELIEF_3"]
            + st.session_state.data_dict["PRE_BELIEF_4"]
            + st.session_state.data_dict["PRE_BELIEF_5"]
        ) / 5
        st.button("下一页", on_click=goToNextPage)
if st.session_state.page_num == 6:
    TOPIC = st.radio(
        "在以下关于转基因的议题中，您认为哪一项对您最重要？",
        ["安全风险", "环境影响", "经济价值", "伦理道德"],
        captions=[
            "对我来说安全吗？",
            "对环境是否有影响？",
            "能降低我的生活成本吗？",
            "修改生物基因是否道德？",
        ],
        index=None,
        key="TOPIC",
    )
    if TOPIC:
        CONCERN_DETAIL = st.text_area(
            label=f"在转基因食品的{TOPIC}上，您可以具体讲讲您的关注点吗？",
            placeholder="请输入大约50-100字。",
            key="CONCERN_DETAIL",
        )
        instruction = (
            "再多写一些可以帮助我们更好地了解您的观点~"
            if len(CONCERN_DETAIL) < 50
            else "可以点击“下一页”继续作答了~"
        )
        st.write(f"您已输入{len(CONCERN_DETAIL)}字。{instruction}")
        if CONCERN_DETAIL:
            st.session_state.data_dict["TOPIC"] = st.session_state.TOPIC
            st.session_state.data_dict["CONCERN_DETAIL"] = (
                st.session_state.CONCERN_DETAIL
            )
            st.button("下一页", on_click=goToNextPage)
if st.session_state.page_num == 7:
    st.write(
        "接下来，您将获得至多五次与AI对话的机会。请您围绕您感兴趣的主题与AI进行交流。"
    )
    if st.session_state.data_dict["GROUP_TIP"] == 1:
        st.write("内容由 AI 生成，请仔细甄别。")
    elif st.session_state.data_dict["GROUP_TIP"] == 2:
        st.write(
            "本 AI 的回答经过了转基因食品领域专家的检查，但不保证完全准确，请仔细甄别。"
        )
    if st.session_state.chat_num >= 1:
        st.button("下一页", on_click=goToNextPage)
    ## 显示聊天历史
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.init_chat:
        st.session_state.init_chat = False
        with st.chat_message("user"):
            init_input = f"你好，我想要了解转基因食品的{st.session_state.data_dict['TOPIC']}。{st.session_state.data_dict['CONCERN_DETAIL']}"
            st.markdown(init_input)
        personalized = st.session_state.data_dict["GROUP_PERSONALIZED"]
        if personalized == 1:
            ## Control Group
            st.session_state.messages.append(
                {
                    "role": "system",
                    "content": "你是一位转基因食品领域的专家，请用150-200词回答用户的相关问题。",
                }
            )
        elif personalized == 2:
            ## Demo Group
            personalized_profile = f'你将面对的用户是一位居住在{st.session_state.data_dict["DEM_RESID"]}的{st.session_state.data_dict["DEM_AGE"]}岁{st.session_state.data_dict["DEM_GENDER_OTHER"] if st.session_state.data_dict["DEM_GENDER_OTHER"] else st.session_state.data_dict["DEM_GENDER"]}，ta的教育程度是{st.session_state.data_dict["DEM_EDU"]}，ta的每月可支配收入约为{st.session_state.data_dict["DEM_INCOME"]}元。**不要透露用户信息。**'
            st.session_state.messages.append(
                {
                    "role": "system",
                    "content": "你是一位转基因食品领域的专家，请用150-200词回答用户的相关问题。"
                    + personalized_profile,
                }
            )
        elif personalized == 3:
            ## PB Group
            if st.session_state.data_dict["PRE_BELIEF"] > 4:
                personalized_profile = "你将要面对的用户对转基因食品存在较深刻的误解，请你谨慎考虑与其交流时的用词。"
            else:
                personalized_profile = "你将要面对的用户对转基因食品的观点是相对乐观的，你可以为ta介绍转基因食品的更多好处。"
            st.session_state.messages.append(
                {
                    "role": "system",
                    "content": "你是一位转基因食品领域的专家，请用150-200词回答用户的相关问题。"
                    + personalized_profile,
                }
            )
        elif personalized == 4:
            ## Demo + PB
            personalized_profile = f'你将面对的用户是一位居住在{st.session_state.data_dict["DEM_RESID"]}的{st.session_state.data_dict["DEM_AGE"]}岁{st.session_state.data_dict["DEM_GENDER_OTHER"] if st.session_state.data_dict["DEM_GENDER_OTHER"] else st.session_state.data_dict["DEM_GENDER"]}，ta的教育程度是{st.session_state.data_dict["DEM_EDU"]}，ta的每月可支配收入约为{st.session_state.data_dict["DEM_INCOME"]}元。**不要透露用户信息。**'
            if st.session_state.data_dict["PRE_BELIEF"] > 4:
                # todo 这里可能需要修改，基于文献的劝服策略
                personalized_profile += "你将要面对的用户对转基因食品存在较深刻的误解，请你谨慎考虑与其交流时的用词。"
            else:
                # todo 这里可能需要修改，基于文献的劝服策略
                personalized_profile += "你将要面对的用户对转基因食品的观点是相对乐观的，你可以为ta介绍转基因食品的更多好处。"
            st.session_state.messages.append(
                {
                    "role": "system",
                    "content": "你是一位转基因食品领域的专家，请用150-200词回答用户的相关问题。"
                    + personalized_profile,
                }
            )
        st.session_state.messages.append({"role": "user", "content": init_input})
        with st.chat_message("assistant"):
            response = st.write_stream(get_response(st.session_state.messages))
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    user_input = st.chat_input(
        f"您还有{5-st.session_state.chat_num}次对话机会，请输入...",
        disabled=st.session_state.chat_disabled,
    )
    if user_input:
        st.session_state.chat_num += 1
        if st.session_state.chat_num >= 5:
            st.session_state.chat_disabled = True
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            response = st.write_stream(get_response(st.session_state.messages))
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

if st.session_state.page_num == 8:
    st.markdown("问卷马上就要结束了，我们还想再问您几个问题。")
    st.markdown("请对以下陈述表明您的同意程度：")
    POST_sat_1 = st.radio(
        "我对与AI的互动非常满意。",
        [
            "完全不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "完全同意",
        ],
        key="POST_sat_1",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    POST_sat_2 = st.radio(
        "我能够理解与AI的互动。",
        [
            "完全不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "完全同意",
        ],
        key="POST_sat_2",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    POST_learning_1 = st.radio(
        "AI帮助我更快地了解转基因食品。",
        [
            "完全不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "完全同意",
        ],
        key="POST_learning_1",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    POST_learning_2 = st.radio(
        "与AI对话后，我对自己的转基因食品认知程度更有信心了。",
        [
            "完全不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "完全同意",
        ],
        key="POST_learning_2",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    POST_continue = st.radio(
        "如果可以，我愿意继续与AI对话。",
        [
            "完全不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "完全同意",
        ],
        key="POST_continue",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    POST_credibility_1 = st.radio(
        "我在本调研中看到的信息是可信的。",
        [
            "完全不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "完全同意",
        ],
        key="POST_credibility_1",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    POST_credibility_2 = st.radio(
        "我在本调研中看到的信息是准确的。",
        [
            "完全不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "完全同意",
        ],
        key="POST_credibility_2",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=True,
    )
    if (
        POST_sat_1
        and POST_sat_2
        and POST_learning_1
        and POST_learning_2
        and POST_continue
        and POST_credibility_1
        and POST_credibility_2
    ):
        st.session_state.data_dict["POST_sat_1"] = st.session_state.POST_sat_1
        st.session_state.data_dict["POST_sat_2"] = st.session_state.POST_sat_2
        st.session_state.data_dict["POST_learning_1"] = st.session_state.POST_learning_1
        st.session_state.data_dict["POST_learning_2"] = st.session_state.POST_learning_2
        st.session_state.data_dict["POST_continue"] = st.session_state.POST_continue
        st.session_state.data_dict["POST_credibility_1"] = (
            st.session_state.POST_credibility_1
        )
        st.session_state.data_dict["POST_credibility_2"] = (
            st.session_state.POST_credibility_2
        )
        st.button("下一页", on_click=goToNextPage)
if st.session_state.page_num == 9:
    st.markdown("最后，我们还想再次询问您对转基因食品的态度。")
    POST_ATTITUDE_1 = st.radio(
        "转基因食品是不好的。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="POST_ATTITUDE_1",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    POST_ATTITUDE_2 = st.radio(
        "转基因食品是令人厌恶的。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="POST_ATTITUDE_2",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    POST_ATTITUDE_3 = st.radio(
        "转基因食品对社会一点用也没有。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="POST_ATTITUDE_3",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    POST_ATTITUDE_4 = st.radio(
        "转基因食品对我的家庭一点用也没有。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="POST_ATTITUDE_4",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    ATTCHECK_2 = st.radio(
        "本题请选择有点同意。",
        [
            "完全不同意",
            "不同意",
            "有点不同意",
            "很难说同意或不同意",
            "有点同意",
            "同意",
            "完全同意",
        ],
        key="ATTCHECK_2",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    POST_WILLING_BUY = st.radio(
        "未来您愿意购买转基因食品吗？",
        [
            "完全不愿意",
            "不愿意",
            "有点不愿意",
            "很难说愿意或不愿意",
            "有点愿意",
            "愿意",
            "完全愿意",
        ],
        key="POST_WILLING_BUY",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    POST_WILLING_EAT = st.radio(
        "未来您愿意食用转基因食品吗？",
        [
            "完全不愿意",
            "不愿意",
            "有点不愿意",
            "很难说愿意或不愿意",
            "有点愿意",
            "愿意",
            "完全愿意",
        ],
        key="POST_WILLING_EAT",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    POST_WILLING_SHARE = st.radio(
        "未来您愿意分享转基因食品给他人吗？",
        [
            "完全不愿意",
            "不愿意",
            "有点不愿意",
            "很难说愿意或不愿意",
            "有点愿意",
            "愿意",
            "完全愿意",
        ],
        key="POST_WILLING_SHARE",
        label_visibility="visible",
        index=None,  # 默认不选中任何选项
        horizontal=False,
    )
    if (
        POST_ATTITUDE_1
        and POST_ATTITUDE_2
        and POST_ATTITUDE_3
        and POST_ATTITUDE_4
        and ATTCHECK_2
        and POST_WILLING_BUY
        and POST_WILLING_EAT
        and POST_WILLING_SHARE
    ):
        st.session_state.data_dict["POST_ATTITUDE_1"] = st.session_state.POST_ATTITUDE_1
        st.session_state.data_dict["POST_ATTITUDE_2"] = st.session_state.POST_ATTITUDE_2
        st.session_state.data_dict["POST_ATTITUDE_3"] = st.session_state.POST_ATTITUDE_3
        st.session_state.data_dict["POST_ATTITUDE_4"] = st.session_state.POST_ATTITUDE_4
        st.session_state.data_dict["ATTCHECK_2"] = st.session_state.ATTCHECK_2
        st.session_state.data_dict["POST_WILLING_BUY"] = (
            st.session_state.POST_WILLING_BUY
        )
        st.session_state.data_dict["POST_WILLING_EAT"] = (
            st.session_state.POST_WILLING_EAT
        )
        st.session_state.data_dict["POST_WILLING_SHARE"] = (
            st.session_state.POST_WILLING_SHARE
        )
        st.button("下一页", on_click=goToNextPage)
if st.session_state.page_num == 10:
    conn = st.connection("postgresql", type="sql")
    st.markdown(
        """感谢您完成了本问卷，请您接下来：
1. 点击「提交」按钮。
2. 根据提示退出系统。"""
    )
    SUBMIT = st.button(
        "提交",
        disabled=st.session_state.submitted,  # 如果已提交则禁用按钮
        key="submit_button",
    )
    data_dict = st.session_state.data_dict
    data_dict["chat_messages"] = st.session_state.messages
    data_dict["chat_num"] = st.session_state.chat_num
    df = pd.DataFrame({k: [v] for k, v in data_dict.items()})
    if SUBMIT:
        st.session_state.submitted = True
        data_dict = st.session_state.data_dict
        data_dict["chat_messages"] = json.dumps(
            st.session_state.messages
        )  # 确保转换为JSON字符串
        data_dict["chat_num"] = st.session_state.chat_num
        try:
            with conn.session as s:
                s.execute(
                    text(
                        """
                    INSERT INTO test 
                    (open_at, group_personalized, group_tip, conscent, code, start_at,
    dem_gender, dem_gender_other, dem_age, dem_resid, dem_edu, dem_income,
    attcheck_1, ailite_1, ailite_2, ailite_3, ailite_4, ailite_5, ailite_6,
    trust_sci_honest, trust_sci_concerned, trust_sci_ethical, trust_sci_improve,
    trust_sci_sincere, trust_sci_otherint, pre_attitude_1, pre_attitude_2,
    pre_attitude_3, pre_attitude_4, pre_willing_buy, pre_willing_eat,
    pre_willing_share, pre_belief_1, pre_belief_2, pre_belief_3, pre_belief_4,
    pre_belief_5, pre_belief, topic, concern_detail, post_sat_1, post_sat_2,
    post_learning_1, post_learning_2, post_continue, post_credibility_1,
    post_credibility_2, post_attitude_1, post_attitude_2, post_attitude_3,
    post_attitude_4, attcheck_2, post_willing_buy, post_willing_eat,
    post_willing_share, chat_messages, chat_num)
                    VALUES (
                        :OpenAt, :GROUP_PERSONALIZED, :GROUP_TIP, :CONSCENT, :CODE, :StartAt,
                        :DEM_GENDER, :DEM_GENDER_OTHER, :DEM_AGE, :DEM_RESID, :DEM_EDU, :DEM_INCOME,
                        :ATTCHECK_1, :AIlit_1, :AIlit_2, :AIlit_3, :AIlit_4, :AIlit_5, :AIlit_6,
                        :TRUST_SCI_honest, :TRUST_SCI_concerned, :TRUST_SCI_ethical, :TRUST_SCI_improve,
                        :TRUST_SCI_sincere, :TRUST_SCI_otherint, :PRE_ATTITUDE_1, :PRE_ATTITUDE_2,
                        :PRE_ATTITUDE_3, :PRE_ATTITUDE_4, :PRE_WILLING_BUY, :PRE_WILLING_EAT,
                        :PRE_WILLING_SHARE, :PRE_BELIEF_1, :PRE_BELIEF_2, :PRE_BELIEF_3, :PRE_BELIEF_4,
                        :PRE_BELIEF_5, :PRE_BELIEF, :TOPIC, :CONCERN_DETAIL, :POST_sat_1, :POST_sat_2,
                        :POST_learning_1, :POST_learning_2, :POST_continue, :POST_credibility_1,
                        :POST_credibility_2, :POST_ATTITUDE_1, :POST_ATTITUDE_2, :POST_ATTITUDE_3,
                        :POST_ATTITUDE_4, :ATTCHECK_2, :POST_WILLING_BUY, :POST_WILLING_EAT,
                        :POST_WILLING_SHARE, :chat_messages, :chat_num
                    )
                """
                    ),
                    data_dict,
                )
                s.commit()
                st.success("提交成功！您可以退出本系统。")
            st.rerun()
        except Exception as e:
            st.error(f"提交失败: {str(e)}")
            st.stop()
    # todo prompt后台的细节如何，论文中需要交代
