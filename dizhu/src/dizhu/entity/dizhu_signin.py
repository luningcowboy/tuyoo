# -*- coding:utf-8 -*-
import json

import datetime

import poker.util.timestamp as pktimestamp
from dizhu.entity import dizhu_util
from poker.entity.biz.content import TYContentItem
from poker.entity.configure import configure
from poker.entity.dao import gamedata
from dizhu.entity.dizhuconf import DIZHU_GAMEID
import freetime.util.log as ftlog

DAYSECONDS = 86400

class SignInDeskData():

    def __init__(self, userId):
        self.userId = userId
        self.signInList = None

    def decodeFromDict(self, d):
        self.signInList = d.get('signInList', [])
        return self

    def toDict(self):
        return {
            'signInList': self.signInList
        }

    def loadData(self):
        hasReceive = False
        expire = False
        jStr = gamedata.getGameAttr(self.userId, DIZHU_GAMEID, 'signInDesk')
        if not jStr:
            return self.decodeFromDict({}), hasReceive, expire
        signInData = self.decodeFromDict(json.loads(jStr))
        signInList = signInData.signInList
        lastSignInTimeStamp = signInList[-1]
        lastSignInDate = datetime.datetime.fromtimestamp(lastSignInTimeStamp).date()
        now = datetime.datetime.now().date()
        timeInterval = (now - lastSignInDate).days

        # # TODO test 每分钟模拟每天
        # lastSignIn = datetime.datetime.strptime(lastSignInStr,"%Y-%m-%d %H:%M:%S").minute
        # now = datetime.datetime.now().minute
        # timeInterval = now - lastSignIn

        receiveDays = len(signInList)
        if timeInterval == 0:
            hasReceive = True
        elif timeInterval == 1:
            if receiveDays >= 7:
                signInData = self.decodeFromDict({})
        else:
            expire = True
            signInData = self.decodeFromDict({})
        return signInData, hasReceive, expire

    def updateSignInList(self):
        now = pktimestamp.getCurrentTimestamp()
        self.signInList.append(now)
        self.saveData()

    def saveData(self):
        gamedata.setGameAttr(self.userId, DIZHU_GAMEID, 'signInDesk', json.dumps(self.toDict()))


def _signInList(userId):
    state = 0
    signInDay = 0
    signInData, hasReceive, _ = SignInDeskData(userId).loadData()
    if not hasReceive:
        state = 1
        signInList = signInData.signInList
        signInDay = len(signInList) + 1

    conf = configure.getGameJson(DIZHU_GAMEID, 'signin', {})
    rewardList = conf.get('rewardList', {})
    return {
        'state': state,
        'signInDay': signInDay,
        'rewardList': rewardList
    }


def _sendRewards(userId, day, typeId):
    signInData, hasReceive, expire = SignInDeskData(userId).loadData()
    if not expire and len(signInData.signInList) != day - 1:
        ftlog.warn('dizhu_signin._sendRewards error day userId=', userId,
                   'day=', day,
                   'typeId=', typeId)
        return 0, []
    if hasReceive:
        ftlog.warn('dizhu_signin._sendRewards has received userId=', userId,
                   'day=', day,
                   'typeId=', typeId)
        return 0, []
    conf = configure.getGameJson(DIZHU_GAMEID, 'signin', {})
    rewardList = conf.get('rewardList', {})
    rewards = []
    if expire:
        rewards = rewardList[0]['rewards']
    else:
        for reward in rewardList:
            if reward.get('day') == day:
                rewards = reward.get('rewards')
    if rewards:
        newRewards = rewards
        if typeId:
            newRewards = []
            for reward in rewards:
                newReward = {}
                newReward['count'] = 2 * reward['count']
                newReward['itemId'] = reward['itemId']
                newReward['pic'] = reward['pic']
                newRewards.append(newReward)
        contentItems = TYContentItem.decodeList(newRewards)
        dizhu_util.sendRewardItems(userId, contentItems, None, 'SIGN_IN_DESK_REWARD', 0)
        signInData.updateSignInList()
        if ftlog.is_debug():
            ftlog.debug('dizhu_signin._sendRewards has rewards',
                        'userId=', userId,
                        'typeId=', typeId,
                        'expire=', expire,
                        'newRewards=', newRewards,
                        'conf=', conf)
        return 1, newRewards
    ftlog.error('dizhu_signin._sendRewards conf error userId=', userId,
               'day=', day,
               'typeId=', typeId,
               'conf=', conf)
    return 0, []

