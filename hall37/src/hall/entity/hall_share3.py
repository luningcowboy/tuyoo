# -*- coding:utf-8 -*-
'''
Created on 2018年5月5日

@author: zhaojiangang
'''

import random
from sre_compile import isstring

import freetime.util.log as ftlog
from hall.entity import datachangenotify, hall_share2
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.hallevent import HallShare3Event
from hall.entity.usercoupon import user_coupon_details
from hall.entity.usercoupon.events import UserCouponReceiveEvent
from poker.entity.biz.exceptions import TYBizConfException
from poker.entity.biz.item.item import TYAssetUtils
from poker.entity.configure import configure, pokerconf
from poker.entity.dao import daobase
from poker.entity.events.tyevent import EventConfigure
import poker.entity.events.tyeventbus as pkeventbus
from poker.util import strutil
import poker.util.timestamp as pktimestamp


class SharePoint3(object):
    def __init__(self):
        # 分享点ID
        self.pointId = None
        # 分享到哪儿给奖励
        self.whereToReward = None
        # 是否分享到不同群condition
        self.condition = {}
        # 分享的文案等内容
        self.weightContents = None
        self.contentsTotalWeight = 0
        # 所属分组的groupId
        self.groupId = None
        # 所属分组
        self.group = None
        # 该分享点奖励 ShareReward
        self._reward = None
    
    @property
    def reward(self):
        return self._reward if not self.group else self.group.reward

    def decodeFromDict(self, d):
        self.pointId = d.get('pointId')
        if not isinstance(self.pointId, int):
            raise TYBizConfException(d, 'SharePoint3.pointId must be int')
        
        self.whereToReward = d.get('whereToReward')
        if not isstring(self.whereToReward) or not self.whereToReward:
            raise TYBizConfException(d, 'SharePoint3.whereToReward must be not empty string')

        self.condition = d.get('condition', {})
        if not isinstance(self.condition, dict):
            raise TYBizConfException(d, 'SharePoint3.condition must be dict')
        
        self.groupId = d.get('groupId')
        if self.groupId is not None and not isinstance(self.groupId, int):
            raise TYBizConfException(d, 'SharePoint3.groupId must be int')
        
        self.desc = d.get('desc', '')
        if not isstring(self.desc):
            raise TYBizConfException(d, 'SharePoint3.desc must be string')
        
        reward = d.get('reward')
        if reward:
            self._reward = hall_share2.ShareReward().decodeFromDict(reward)
        
        self.weightContents = []
        weightContents = d.get('contents')
        if not isinstance(weightContents, list):
            raise TYBizConfException(d, 'SharePoint3.contents must be list')
        
        self.contentsTotalWeight = 0
        for weightContent in weightContents:
            weight = weightContent.get('weight')
            if not isinstance(weight, int) or weight < 0:
                raise TYBizConfException(d, 'SharePoint3.contents.item.weight must be int > 0')
            content = weightContent.get('content')
            if not isinstance(content, dict):
                raise TYBizConfException(d, 'SharePoint3.contents.item.content must be dict')
            self.weightContents.append(((self.contentsTotalWeight, self.contentsTotalWeight + weight), content))
            self.contentsTotalWeight += weight
        return self


class SharePointGroup3(object):
    def __init__(self):
        # 分组ID
        self.groupId = None
        # 该分组奖励 ShareReward
        self.reward = None

    def decodeFromDict(self, d):
        self.groupId = d.get('groupId')
        if not isinstance(self.groupId, int):
            raise TYBizConfException(d, 'SharePointGroup.groupId must be int')
        
        reward = d.get('reward')
        if reward:
            self.reward = hall_share2.ShareReward().decodeFromDict(reward)
        
        return self


# 初始化标记
_inited = False
# map<gameId, map<sharePointId, SharePoint3> >
_gameSharePointMap = {}
# 分组配置 map<gameId, map<groupId, SharePointGroup> >
_gameSharePointGroupMap = {}


def getSharePoint(gameId, userId, clientId, pointId):
    '''
    获取分享点
    '''
    hallGameId = gameId if gameId != 9999 else strutil.getGameIdFromHallClientId(clientId)
    return _gameSharePointMap.get(hallGameId, {}).get(pointId)

def getShareContent(userId, clientId, sharePoint):
    if sharePoint.contentsTotalWeight > 0:
        v = random.randint(0, sharePoint.contentsTotalWeight - 1)
        for (s, e), content in sharePoint.weightContents:
            if v >= s and v < e:
                return content
    return random.choice(sharePoint.weightContents)[1]

def getBurials(gameId, userId, clientId):
    hallGameId = gameId if gameId != 9999 else strutil.getGameIdFromHallClientId(clientId)
    return configure.getTcContentByGameId('share3', None, hallGameId, clientId, {})

def getSharePointByBurialId(gameId, userId, clientId, burialId):
    burials = getBurials(gameId, userId, clientId)
    if ftlog.is_debug():
        ftlog.warn('hall_share3.getSharePointByBurialId',
                   'gameId=', gameId,
                   'userId=', userId,
                   'clientId=', clientId,
                   'burials=', [burial.get('burialId') for burial in burials])
    for burial in burials:
        if burial['burialId'] == burialId:
            pointId = burial.get('pointId')
            sharePoint = getSharePoint(gameId, userId, clientId, pointId)
            if not sharePoint:
                ftlog.warn('hall_share3.getSharePointByBurialId NoSharePoint',
                           'gameId=', gameId,
                           'userId=', userId,
                           'clientId=', clientId,
                           'burialId=', burialId,
                           'pointId=', pointId)
            return sharePoint
    
    ftlog.warn('hall_share3.getSharePointByBurialId NotBurialId',
               'gameId=', gameId,
               'userId=', userId,
               'clientId=', clientId,
               'burialId=', burialId)

    return None

def buildShareTodoTask(gameId, userId, clientId, pointId, urlParams):
    from hall.entity.todotask import TodoTaskShare3Share
    
    sharePoint = getSharePoint(gameId, userId, clientId, pointId)
    if not sharePoint:
        ftlog.warn('hall_share3.buildShareTodoTask UnknownSharePoint',
                   'gameId=', gameId,
                   'userId=', userId,
                   'clientId=', clientId,
                   'pointId=', pointId)
        return None
    
    shareContent = getShareContent(userId, clientId, sharePoint)
    return TodoTaskShare3Share(pointId,
                               sharePoint.whereToReward,
                               strutil.replaceParams(shareContent.get('title', ''), urlParams),
                               shareContent.get('pic', ''))

def getStatusField(sharePoint):
    return 'pt:%s' % (sharePoint.pointId) if not sharePoint.group else 'gp:%s' % (sharePoint.groupId)

def loadShareStatus(gameId, userId, sharePoint, timestamp):
    jstr = None
    key = 'share3.status:%s:%s' % (gameId, userId)
    field = getStatusField(sharePoint)
    
    try:
        jstr = daobase.executeUserCmd(userId, 'hget', key, field)
        if ftlog.is_debug():
            ftlog.debug('hall_share3.loadShareStatus',
                        'gameId=', gameId,
                        'userId=', userId,
                        'pointId=', sharePoint.pointId,
                        'groupId=', sharePoint.groupId,
                        'field=', field,
                        'timestamp=', timestamp,
                        'jstr=', jstr)
        if jstr:
            d = strutil.loads(jstr)
            if ftlog.is_debug():
                ftlog.debug('hall_share3.loadShareStatus',
                            'gameId=', gameId,
                            'userId=', userId,
                            'pointId=', sharePoint.pointId,
                            'groupId=', sharePoint.groupId,
                            'field=', field,
                            'timestamp=', timestamp,
                            'jstr=', jstr,
                            'd=', d,
                            'isSameCycle=', sharePoint.reward.cycle.timeCycle.isSameCycle(d['ts'], timestamp))
            if sharePoint.reward and not sharePoint.reward.cycle.timeCycle.isSameCycle(d['ts'], timestamp):
                d['ts'] = timestamp
                d['rct'] = 0
            return d['ts'], d['rct']
    except:
        ftlog.error('hall_share3.getShareStatus',
                    'userId=', userId,
                    'pointId=', sharePoint.pointId,
                    'groupId=', sharePoint.groupId,
                    'field=', field,
                    'timestamp=', timestamp,
                    'jstr=', jstr)
    return timestamp, 0

def saveShareStatus(gameId, userId, sharePoint, timestamp, rewardCount):
    jstr = strutil.dumps({'ts':timestamp, 'rct':rewardCount})
    key = 'share3.status:%s:%s' % (gameId, userId)
    field = getStatusField(sharePoint)
    daobase.executeUserCmd(userId, 'hset', key, field, jstr)
    if ftlog.is_debug():
        ftlog.debug('hall_share3.saveShareStatus',
                    'gameId=', gameId,
                    'userId=', userId,
                    'pointId=', sharePoint.pointId,
                    'groupId=', sharePoint.groupId,
                    'field=', field,
                    'timestamp=', timestamp,
                    'jstr=', jstr)

def sendReward(gameId, userId, sharePoint):
    from hall.entity import hallitem
    if not sharePoint.reward or not sharePoint.reward.content:
        return None

    userAssets = hallitem.itemSystem.loadUserAssets(userId)
    assetList = userAssets.sendContent(gameId, sharePoint.reward.content, 1, True,
                                       pktimestamp.getCurrentTimestamp(),
                                       'SHARE3_REWARD', sharePoint.pointId)
    ftlog.info('hall_share3.sendReward',
               'gameId=', gameId,
               'userId=', userId,
               'pointId=', sharePoint.pointId,
               'groupId=', sharePoint.groupId,
               'rewards=', [(atup[0].kindId, atup[1]) for atup in assetList])
    changedDataNames = TYAssetUtils.getChangeDataNames(assetList)
    datachangenotify.sendDataChangeNotify(gameId, userId, changedDataNames)
    for atup in assetList:
        if atup[0].kindId == 'user:coupon':
            # 广播事件
            from hall.game import TGHall
            TGHall.getEventBus().publishEvent(
                UserCouponReceiveEvent(HALL_GAMEID, userId, atup[1], user_coupon_details.USER_COUPON_SHARE3))

    return assetList

def getRewardCount(gameId, userId, sharePoint, timestamp):
    _, rewardCount = loadShareStatus(gameId, userId, sharePoint, timestamp)
    sharePointCount = sharePoint.reward.cycle.count if sharePoint.reward else 0
    return min(rewardCount, sharePointCount), sharePointCount

def getShareLeftCountByBurialId(gameId, userId, clientId, burialId):
    ''' 获取分享埋点剩余次数 '''
    sharePoint = getSharePointByBurialId(gameId, userId, clientId, burialId)
    rewardCount, totalRewardCount = getRewardCount(gameId, userId, sharePoint, pktimestamp.getCurrentTimestamp())
    return totalRewardCount - rewardCount

def incrRewardCount(gameId, userId, sharePoint, timestamp):
    _, rewardCount = loadShareStatus(gameId, userId, sharePoint, timestamp)
    
    if sharePoint.reward.cycle.count != -1 and rewardCount >= sharePoint.reward.cycle.count:
        return False, rewardCount
    
    rewardCount += 1
    saveShareStatus(gameId, userId, sharePoint, timestamp, rewardCount)
    
    return True, rewardCount

def sendRewardIfNeed(gameId, userId, clientId, sharePoint, timestamp):
    ok, rewardCount = incrRewardCount(gameId, userId, sharePoint, timestamp)
    if not ok:
        if ftlog.is_debug():
            ftlog.debug('hall_share3.gainShareReward UpperLimit',
                        'gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'pointId=', sharePoint.pointId,
                        'rewardCount=', rewardCount,
                        'maxRewardCount=', sharePoint.reward.cycle.count)
        return False, None

    rewards = sendReward(gameId, userId, sharePoint)
    return True, rewards

def gainShareReward(gameId, userId, clientId, pointId, whereToShare, timestamp=None):
    sharePoint = getSharePoint(gameId, userId, clientId, pointId)
    from hall.game import TGHall
    
    if not sharePoint:
        ftlog.warn('hall_share3.gainShareReward UnknownSharePoint',
                   'gameId=', gameId,
                   'userId=', userId,
                   'clientId=', clientId,
                   'pointId=', pointId,
                   'whereToShare=', whereToShare)
        return False, None
    
    if (sharePoint.whereToReward != 'all'
        and whereToShare != sharePoint.whereToReward):
        if ftlog.is_debug():
            ftlog.debug('hall_share3.gainShareReward UnknownSharePoint',
                        'gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'pointId=', pointId,
                        'whereToShare=', whereToShare)
        return False, None
    
    if not sharePoint.reward:
        if ftlog.is_debug():
            ftlog.debug('hall_share3.gainShareReward NotHaveReward',
                        'gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'pointId=', pointId,
                        'whereToShare=', whereToShare)
        TGHall.getEventBus().publishEvent(HallShare3Event(gameId, userId, pointId, None))
        return False, None
    
    timestamp = timestamp or pktimestamp.getCurrentTimestamp()
    
    ok, rewardCount = incrRewardCount(gameId, userId, sharePoint, timestamp)
    if not ok:
        TGHall.getEventBus().publishEvent(HallShare3Event(gameId, userId, pointId, None))
        if ftlog.is_debug():
            ftlog.debug('hall_share3.gainShareReward UpperLimit',
                        'gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'pointId=', sharePoint.pointId,
                        'whereToShare=', whereToShare,
                        'rewardCount=', rewardCount,
                        'maxRewardCount=', sharePoint.reward.cycle.count)
        return False, None
    
    rewards = sendReward(gameId, userId, sharePoint)
    TGHall.getEventBus().publishEvent(HallShare3Event(gameId, userId, pointId, rewards))
    return True, rewards

def _onConfChanged(event):
    if _inited and event.isModuleChanged('share3'):
        for gameId in pokerconf.getConfigGameIds():
            if event.isChanged('game:%s:share3:0' % (gameId)):
                _reloadGameConf(gameId)

def _reloadGameConf(gameId):
    sharePointMap, sharePointGroupMap = _loadGameConf(gameId)
    if sharePointMap:
        _gameSharePointMap[gameId] = sharePointMap
    else:
        _gameSharePointMap.pop(gameId, None)
    
    if sharePointGroupMap:
        _gameSharePointGroupMap[gameId] = sharePointGroupMap
    else:
        _gameSharePointGroupMap.pop(gameId, None)
        
    ftlog.info('hall_share3._reloadGameConf',
               'gameId=', gameId,
               'sharePointGroups=', sharePointGroupMap.keys() if sharePointGroupMap else None,
               'sharePoints=', [(sharePoint.pointId, sharePoint.groupId) for sharePoint in sharePointMap.values()] if sharePointMap else None)

def _reloadConf():
    _gameSharePointMap.clear()
    for gameId in pokerconf.getConfigGameIds():
        _reloadGameConf(gameId)

def _initialize():
    global _inited
    if not _inited:
        _inited = True
        _reloadConf()
        pkeventbus.globalEventBus.subscribe(EventConfigure, _onConfChanged)

def _loadGameConf(gameId):
    conf = configure.getGameJson(gameId, 'share3', {}, 0)
    if not conf:
        return None, None
    
    sharePointMap = {}
    sharePointGroupMap = {}
    
    for gp in conf.get('groups', []):
        sharePointGroup = SharePointGroup3().decodeFromDict(gp)
        if sharePointGroup.groupId in sharePointGroupMap:
            raise TYBizConfException(gp, 'Duplicate sharePointGroupId %s' % (sharePointGroup.groupId))
        sharePointGroupMap[sharePointGroup.groupId] = sharePointGroup

    if ftlog.is_debug():
        ftlog.debug('hall_share3._loadGameConf',
                    'gameId=', gameId,
                    'groupIds=', sharePointGroupMap.keys())

    for sp in conf.get('points', []):
        sharePoint = SharePoint3().decodeFromDict(sp)
        if sharePoint.pointId in sharePointMap:
            raise TYBizConfException(sp, 'Duplicate sharePointId %s' % (sharePoint.pointId))
        if sharePoint.groupId:
            group = sharePointGroupMap.get(sharePoint.groupId)
            if not group:
                raise TYBizConfException(sp, 'Not found groupId %s for sharePoint %s' % (sharePoint.groupId, sharePoint.pointId))
            sharePoint.group = group
        sharePointMap[sharePoint.pointId] = sharePoint
    
    return sharePointMap, sharePointGroupMap


