# -*- coding:utf-8 -*-
'''
Created on 2018-08-20

@author: wangyonghui

功能： 引导添加我的小程序
'''
from sre_compile import isstring

from dizhu.entity import dizhu_util
from dizhu.entity.dizhuconf import DIZHU_GAMEID
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.usercoupon import user_coupon_details
from hall.entity.usercoupon.events import UserCouponReceiveEvent
from hall.game import TGHall
from poker.entity.biz.content import TYContentItem
from poker.entity.biz.exceptions import TYBizConfException
from poker.entity.configure import configure
from poker.entity.dao import gamedata
from poker.entity.events.tyevent import EventConfigure
import poker.entity.events.tyeventbus as pkeventbus
import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from poker.util import strutil


class RewardItem(object):
    def __init__(self):
        self.startCount = None
        self.endCount = None
        self.rewardDesc = None
        self.rewardPic = None
        self.rewards = None
        self.rewardsConf = None

    def decodeFromDict(self, d):
        self.startCount = d.get('startCount')
        if not isinstance(self.startCount, int):
            raise TYBizConfException(d, 'WXFollowConf.RewardItem.startCount must be int')

        self.endCount = d.get('endCount')
        if not isinstance(self.endCount, int):
            raise TYBizConfException(d, 'WXFollowConf.RewardItem.endCount must be int')

        self.rewardDesc = d.get('rewardDesc')
        if not isstring(self.rewardDesc):
            raise TYBizConfException(d, 'WXFollowConf.RewardItem.rewardDesc must be str')

        self.rewardPic = d.get('rewardPic')
        if not isstring(self.rewardPic):
            raise TYBizConfException(d, 'WXFollowConf.RewardItem.rewardPic must be str')

        rewards = d.get('rewards')
        if not isinstance(rewards, list):
            raise TYBizConfException(d, 'WXFollowConf.RewardItem.rewards must be list')
        try:
            self.rewards = TYContentItem.decodeList(rewards)
            self.rewardsConf = rewards
        except Exception, e:
            raise TYBizConfException(d, 'WXFollowConf.RewardItem.rewards err=%s' % e.message)
        return self

    def toDict(self):
        return {
            'rewardDesc': self.rewardDesc,
            'rewardPic': self.rewardPic,
            'rewards': self.rewardsConf
        }


class WXFollowConf(object):
    ''' 配置 '''
    def __init__(self):
        self.cycleSeconds = None
        self.rewardList = None

    def decodeFromDict(self, d):
        self.cycleSeconds = d.get('cycleSeconds')
        if not isinstance(self.cycleSeconds, int):
            raise TYBizConfException(d, 'WXFollowConf.cycleSeconds must be int')

        rewardList = d.get('rewardList')
        if not isinstance(rewardList, list):
            raise TYBizConfException(d, 'WXFollowConf.rewardList must be list')
        self.rewardList = [RewardItem().decodeFromDict(d) for d in rewardList]
        return self

    def getRewardByCount(self, count):
        for reward in self.rewardList:
            if (reward.startCount == -1 or reward.startCount <= count) and (reward.endCount == -1 or reward.endCount >= count):
                return reward
        return None


class UserWxFollowData(object):
    ''' 用户数据抽象 '''
    def __init__(self, userId):
        self.userId = userId
        self.count = 0
        self.timestamp = 0

    def loadData(self):
        jstr = gamedata.getGameAttr(self.userId, DIZHU_GAMEID, 'wxFollowCount')
        if jstr:
            jdict = strutil.loads(jstr)
            return self.decodeFromDict(jdict)
        return self

    def saveData(self):
        gamedata.setGameAttr(self.userId, DIZHU_GAMEID, 'wxFollowCount', strutil.dumps(self.toDict()))

    def increaseFollowCount(self, step=1):
        self.count += step
        self.timestamp = pktimestamp.getCurrentTimestamp()
        self.saveData()

    def decodeFromDict(self, d):
        self.count = d.get('count', 0)
        self.timestamp = d.get('timestamp', pktimestamp.getCurrentTimestamp())
        return self

    def toDict(self):
        return {
            'count': self.count,
            'timestamp': self.timestamp
        }


class WxFollowHelper(object):
    ''' 对外接口类 '''
    @classmethod
    def wxFollowInfo(cls, userId):
        ''' 登录接口就返回 '''
        userData = UserWxFollowData(userId).loadData()
        if pktimestamp.getCurrentTimestamp() - userData.timestamp < _wxFollowConf.cycleSeconds:
            return None
        rewardObj = _wxFollowConf.getRewardByCount(userData.count)
        if rewardObj:
            return rewardObj.toDict()
        return None

    @classmethod
    def sendUserReward(cls, userId):
        userData = UserWxFollowData(userId).loadData()
        if pktimestamp.getCurrentTimestamp() - userData.timestamp < _wxFollowConf.cycleSeconds:
            return None

        rewardObj = _wxFollowConf.getRewardByCount(userData.count)
        if rewardObj:
            dizhu_util.sendRewardItems(userId, rewardObj.rewards, '', 'DIZHU_WX_FOLLOW', userData.count)
            userData.increaseFollowCount()
            for reward in rewardObj.rewardsConf:
                if reward['itemId'] == 'user:coupon':
                    TGHall.getEventBus().publishEvent(
                        UserCouponReceiveEvent(HALL_GAMEID, userId, reward['count'], user_coupon_details.USER_COUPON_WX_FOLLOW))
            return rewardObj.toDict()
        return None


_inited = False
_wxFollowConf = None


def _reloadConf():
    global _wxFollowConf
    conf = configure.getGameJson(DIZHU_GAMEID, 'wx.follow', {})
    _wxFollowConf = WXFollowConf().decodeFromDict(conf)
    ftlog.info('wx_follow._reloadConf success _wxFollowConf=', _wxFollowConf)


def _onConfChanged(event):
    if _inited and event.isChanged(['game:6:wx.follow:0']):
        _reloadConf()


def _initialize():
    global _inited
    if not _inited:
        _inited = True
        _reloadConf()
        pkeventbus.globalEventBus.subscribe(EventConfigure, _onConfChanged)
    ftlog.info('wx_follow._initialize ok')
